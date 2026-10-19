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
            return handler(prepared.override(messages=add_file_names(list(prepared.messages))))

        return super().wrap_model_call(request, with_filenames)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ):
        async def with_filenames(prepared: ModelRequest):
            if self.controls:
                prepared = self.controls.model_request(prepared)
            return await handler(
                prepared.override(messages=add_file_names(list(prepared.messages)))
            )

        return await super().awrap_model_call(request, with_filenames)

    def wrap_tool_call(self, request, handler):
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
