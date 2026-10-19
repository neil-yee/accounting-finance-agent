"""Expose persistent approved memory and skills through local filesystem routes."""

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import (
    BackendProtocol,
    DeleteResult,
    EditResult,
    FileUploadResponse,
    WriteResult,
)

from accounting_finance_agent.config import PROJECT_ROOT


MEMORY_ROOT = PROJECT_ROOT / "memory"
SKILLS_ROOT = PROJECT_ROOT / "skills"
MEMORY_PATH = "/memories/AGENTS.md"
SKILLS_PATH = "/skills/"

APPROVED_MEMORY_PROMPT = """<approved_agent_memory>
{agent_memory}
</approved_agent_memory>

These are owner-maintained, read-only reference files shared across conversations.
Use relevant guidance while following the current user's instructions and verified evidence.
Never store credentials in memory. Do not edit approved memory or skills yourself.
"""


class ApprovedFilesBackend(FilesystemBackend):
    """Allow reads while denying every backend mutation of approved files."""

    def write(self, file_path: str, content: str) -> WriteResult:
        return WriteResult(error="Reference files are read-only and maintained by the owner.")

    def edit(
        self, file_path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
        return EditResult(error="Reference files are read-only and maintained by the owner.")

    def delete(self, file_path: str) -> DeleteResult:
        return DeleteResult(error="Approved reference files are read-only.")

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        return [FileUploadResponse(path=path, error="permission_denied") for path, _ in files]


def knowledge_backend(execution_backend: BackendProtocol | None = None) -> CompositeBackend:
    """Keep approved files on the host; leave ordinary file operations on the default."""
    for folder in (MEMORY_ROOT, SKILLS_ROOT):
        if folder.is_symlink() or folder.is_junction():
            raise ValueError(f"Approved reference folders must not be links: {folder}")
        folder.mkdir(parents=True, exist_ok=True)
    return CompositeBackend(
        default=execution_backend if execution_backend is not None else StateBackend(),
        routes={
            "/memories/": ApprovedFilesBackend(root_dir=MEMORY_ROOT, virtual_mode=True),
            SKILLS_PATH: ApprovedFilesBackend(root_dir=SKILLS_ROOT, virtual_mode=True),
        },
    )
