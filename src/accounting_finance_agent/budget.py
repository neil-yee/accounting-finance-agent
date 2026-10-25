"""Count and reserve every synchronous provider attempt, including compaction."""

from decimal import Decimal
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import json
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
        if any(kind in request.content for kind in (b'"input_image"', b'"input_file"', b'"input_audio"')):
            raise RunLimitExceeded('Binary provider inputs are unsupported in the text-only benchmark; use sandbox libraries.')
        input_bound = len(request.content) + 8192
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
