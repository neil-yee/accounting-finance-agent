"""Count and reserve every synchronous provider attempt, including compaction."""

from decimal import Decimal
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import json
import base64
from hashlib import sha256
import random
import time
import httpx

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.runtime import RunLimitExceeded


class BudgetClient(httpx.Client):
    def __init__(self, controls, **kwargs):
        super().__init__(**kwargs)
        self.controls = controls
        self.card = json.loads((PROJECT_ROOT / 'config/model-pricing.json').read_text())
        self.spent = Decimal(0)
        self.limit = Decimal(self.card['budget_usd'])
        self.image_token_counts = {}

    def image_input_bound(self, body, request):
        """Count immutable embedded images once; keep bytes out of the text bound.

        The provider token-count endpoint does not generate model output. Its
        HTTP requests consume the shared request/time ceilings and are logged.
        Unavailable/invalid counts stop before any generation request is sent.
        """
        image_tokens = 0

        def convert(value):
            nonlocal image_tokens
            if isinstance(value, list):
                return [convert(item) for item in value]
            if not isinstance(value, dict):
                return value
            kind = value.get('type')
            if kind in {'input_file', 'input_audio', 'input_video'}:
                raise RunLimitExceeded('Unsupported direct file/audio/video input; use sandbox libraries.')
            if kind != 'input_image':
                return {key: convert(item) for key, item in value.items()}
            url = value.get('image_url', '')
            allowed = ('data:image/png;base64,', 'data:image/jpeg;base64,',
                       'data:image/webp;base64,', 'data:image/gif;base64,')
            if not isinstance(url, str) or not url.startswith(allowed):
                raise RunLimitExceeded('Image inputs must be embedded PNG/JPEG/WebP/GIF data; remote URLs/file IDs are not budgeted.')
            encoded = url.split(',', 1)[1]
            if len(encoded) > 14 * 1024**2:
                raise RunLimitExceeded('Image exceeds the 10 MiB input limit.')
            try:
                raw = base64.b64decode(encoded, validate=True)
            except ValueError as exc:
                raise RunLimitExceeded('Invalid image encoding.') from exc
            if len(raw) > 10 * 1024**2:
                raise RunLimitExceeded('Image exceeds the 10 MiB input limit.')
            identity = sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
            if identity not in self.image_token_counts:
                self.controls.reserve('model', image_token_preflight=True)
                count_body = {'model': body['model'], 'input': [
                    {'role': 'user', 'content': [value]}]}
                headers = dict(request.headers)
                headers.pop('content-length', None)
                endpoint = request.url.copy_with(path=request.url.path.rstrip('/') + '/input_tokens')
                count_request = self.build_request('POST', endpoint, headers=headers, json=count_body,
                    timeout=min(self.controls.remaining(), self.controls.settings.model_timeout_seconds))
                response = super(BudgetClient, self).send(count_request, stream=False, follow_redirects=False)
                try:
                    response.raise_for_status()
                    count = response.json().get('input_tokens')
                    if type(count) is not int or count <= 0:
                        raise RunLimitExceeded('Provider did not return a valid image token count.')
                finally:
                    response.close()
                self.image_token_counts[identity] = count
                self.controls.log.event(self.controls.context.run_id, 'image_token_count',
                                        image_sha256=identity, input_tokens=count)
            image_tokens += self.image_token_counts[identity]
            return {**value, 'image_url': '[embedded image counted separately]'}

        text_body = convert(body)
        return len(json.dumps(text_body).encode()) + 8192 + image_tokens

    def send(self, request, **kwargs):
        body = json.loads(request.content)
        if (body.get('model') != self.card['model'] or body.get('stream')
                or body.get('service_tier', 'default') != self.card['service_tier']):
            raise RunLimitExceeded('Unpriced model/tier or streaming request rejected.')
        if any(tool.get('type') != 'function' for tool in body.get('tools', [])):
            raise RunLimitExceeded('Unpriced provider-hosted tools are unavailable in this benchmark.')
        input_rate = Decimal(self.card['input_usd_per_million']) / 1_000_000
        output_rate = Decimal(self.card['output_usd_per_million']) / 1_000_000
        # UTF-8 bytes bound text tokens; overhead covers framing/tool wrappers.
        if body.get('previous_response_id') or body.get('conversation'):
            raise RunLimitExceeded('Server-side hidden history is outside the reservation contract.')
        with self.controls.lock:
            if self.spent >= self.limit:
                raise RunLimitExceeded('API budget exhausted before input inspection.')
        input_bound = self.image_input_bound(body, request)
        with self.controls.lock:
            available = self.limit - self.spent - input_bound * input_rate
            cap = min(body.get('max_output_tokens', 32000), int(available / output_rate))
            if cap < 1:
                raise RunLimitExceeded('Insufficient API budget for the next request.')
            body['max_output_tokens'] = cap
            reservation = input_bound * input_rate + cap * output_rate
        content = json.dumps(body).encode()
        for attempt in range(6):
            with self.controls.lock:
                if self.spent + reservation > self.limit:
                    raise RunLimitExceeded('API budget exhausted before retry.')
                self.controls.reserve('model', api_attempt=True, retry=attempt)
                self.spent += reservation
                self.controls.log.event(self.controls.context.run_id, 'api_reserved',
                                        usd=str(reservation), committed_usd=str(self.spent),
                                        rate_card=self.card['version'])
            remaining = self.controls.remaining()
            headers = dict(request.headers)
            headers.pop('content-length', None)
            current = self.build_request(request.method, request.url, headers=headers, content=content,
                                         timeout=min(remaining, self.controls.settings.model_timeout_seconds))
            response = None
            try:
                response = super().send(current, **{**kwargs, 'stream': False, 'follow_redirects': False})
                response.read()
                if response.is_success:
                    payload = response.json()
                    usage = payload.get('usage')
                    if usage:
                        actual = Decimal(usage['input_tokens']) * input_rate + Decimal(usage['output_tokens']) * output_rate
                        with self.controls.lock:
                            # Never refund an underestimated/unknown attempt.
                            self.spent += actual - reservation
                        self.controls.log.event(self.controls.context.run_id, 'api_usage', usage=usage,
                                                estimated_usd=str(actual), committed_usd=str(self.spent),
                                                provider_model=payload.get('model'), service_tier=payload.get('service_tier'),
                                                response_id=payload.get('id'))
                        if actual > reservation:
                            raise RunLimitExceeded('Usage exceeded reservation; stop and reconcile pricing.')
                    return response
                if response.status_code not in {408, 409, 429, 500, 502, 503, 504}:
                    return response
            except (httpx.TimeoutException, httpx.NetworkError):
                # Unknown usage retains the full reservation.
                pass
            if attempt == 5:
                if response is not None:
                    return response
                raise RunLimitExceeded('Six provider attempts exhausted.')
            delay = 2 ** attempt + random.random()
            if response is not None:
                header = response.headers.get('retry-after')
                if header:
                    try:
                        delay = max(delay, float(header))
                    except ValueError:
                        delay = max(delay, (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds())
                response.close()
            if delay >= self.controls.remaining():
                raise RunLimitExceeded('Retry delay cannot fit the remaining deadline.')
            print(f'Retry {attempt + 1} of 5', flush=True)
            self.controls.log.event(self.controls.context.run_id, 'api_retry', number=attempt + 1, delay=delay)
            time.sleep(delay)
        raise AssertionError('unreachable')


class DisabledAsyncClient(httpx.AsyncClient):
    async def send(self, request, **kwargs):
        raise RunLimitExceeded('Benchmark API execution uses the metered synchronous runner only.')
