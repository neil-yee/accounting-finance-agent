"""Supply filenames omitted from binary reads by the pinned Deep Agents version."""

from collections.abc import Awaitable, Callable
import mimetypes
from pathlib import PurePosixPath

from deepagents.middleware.filesystem import FilesystemMiddleware
from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage


def add_file_names(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Return request-only copies with filenames; leave saved messages unchanged."""
    read_paths = {
        call["id"]: call["args"].get("file_path")
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
        if call["name"] == "read_file"
    }
    result = []
    for message in messages:
        if not isinstance(message.content, list):
            result.append(message)
            continue
        path = message.additional_kwargs.get("read_file_path")
        if not path and isinstance(message, ToolMessage):
            path = read_paths.get(message.tool_call_id)
        filename = (
            PurePosixPath(path.replace("\\", "/")).name
            if isinstance(path, str) else ""
        )
        content = []
        changed = False
        for block in message.content:
            if (
                isinstance(block, dict)
                and block.get("type") == "file"
                and ("base64" in block or block.get("source_type") == "base64")
                and not block.get("filename")
                and not (block.get("extras") or {}).get("filename")
                and not (block.get("metadata") or {}).get("filename")
            ):
                extension = mimetypes.guess_extension(block.get("mime_type", "")) or ".bin"
                content.append({**block, "filename": filename or f"attachment{extension}"})
                changed = True
            else:
                content.append(block)
        result.append(message.model_copy(update={"content": content}) if changed else message)
    return result


def text_only_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Keep unsupported media out of priced text-only requests, with an explanation.

    Saved tool results stay intact for the human reviewer; only the outgoing
    request is adapted. The model must not claim it visually inspected previews.
    """
    result = []
    media = {"image", "image_url", "input_image", "file", "input_file",
             "audio", "input_audio", "video"}
    for message in messages:
        if not isinstance(message.content, list):
            result.append(message)
            continue
        content = []
        changed = False
        for block in message.content:
            if isinstance(block, dict) and block.get("type") in media:
                name = block.get("filename", "binary attachment")
                content.append({"type": "text", "text": (
                    f"{name}: binary content is available to the reviewer but is not "
                    "supported by this text-only run. Inspect file structure/text using "
                    "sandbox libraries. Report visual inspection as unavailable to you; "
                    "do not retry reading image previews or claim you saw them."
                )})
                changed = True
            else:
                content.append(block)
        result.append(message.model_copy(update={"content": content}) if changed else message)
    return result


class FileMetadataFilesystemMiddleware(FilesystemMiddleware):
    """Retain filesystem behavior while repairing outgoing file metadata.

    The matching middleware name replaces the default filesystem slot rather
    than adding duplicate tools. Deep Agents also inherits this slot override
    into its default general-purpose subagent.
    """

    def __init__(self, *args, controls=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.controls = controls

    @property
    def name(self) -> str:
        return "FilesystemMiddleware"

    def wrap_model_call(
        self, request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]
    ):
        def with_filenames(prepared: ModelRequest):
            if self.controls:
                prepared = self.controls.model_request(prepared)
            messages = add_file_names(list(prepared.messages))
            from accounting_finance_agent.config import EXCEL_PROFILE
            if self.controls and self.controls.settings.profile == EXCEL_PROFILE:
                messages = text_only_messages(messages)
            return handler(prepared.override(messages=messages))

        return super().wrap_model_call(request, with_filenames)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ):
        async def with_filenames(prepared: ModelRequest):
            if self.controls:
                prepared = self.controls.model_request(prepared)
            messages = add_file_names(list(prepared.messages))
            from accounting_finance_agent.config import EXCEL_PROFILE
            if self.controls and self.controls.settings.profile == EXCEL_PROFILE:
                messages = text_only_messages(messages)
            return await handler(prepared.override(messages=messages))

        return await super().awrap_model_call(request, with_filenames)

    def wrap_tool_call(self, request, handler):
        from accounting_finance_agent.config import EXCEL_PROFILE
        from langsmith.sandbox import SandboxConnectionError
        if self.controls and self.controls.settings.profile == EXCEL_PROFILE:
            import random
            import time
            # Reconcile writes explicitly; only read operations are replayable.
            safe = request.tool_call['name'] in {'ls', 'read_file', 'glob', 'grep'}
            for attempt in range(6):
                try:
                    return self._one_tool_call(request, handler)
                except (ConnectionError, TimeoutError, SandboxConnectionError):
                    if not safe or attempt == 5:
                        raise
                    delay = 2 ** attempt + random.random()
                    if delay >= self.controls.remaining():
                        from accounting_finance_agent.runtime import RunLimitExceeded
                        raise RunLimitExceeded('Tool retry cannot fit the remaining deadline.')
                    print(f'Retry {attempt + 1} of 5: {request.tool_call["name"]}', flush=True)
                    self.controls.log.event(self.controls.context.run_id, 'tool_retry',
                                            number=attempt + 1, delay=delay)
                    time.sleep(delay)
        return self._one_tool_call(request, handler)

    def _one_tool_call(self, request, handler):
        if self.controls:
            self.controls.tool_started(request)
            request = self.controls.prepare_tool_request(request)
        try:
            result = super().wrap_tool_call(request, handler)
        except BaseException as exc:
            if self.controls:
                self.controls.tool_finished(request, error=exc)
            raise
        if self.controls:
            self.controls.tool_finished(request, result=result)
        return result

    async def awrap_tool_call(self, request, handler):
        if self.controls:
            self.controls.tool_started(request)
            request = self.controls.prepare_tool_request(request)
        try:
            result = await super().awrap_tool_call(request, handler)
        except BaseException as exc:
            if self.controls:
                self.controls.tool_finished(request, error=exc)
            raise
        if self.controls:
            self.controls.tool_finished(request, result=result)
        return result
