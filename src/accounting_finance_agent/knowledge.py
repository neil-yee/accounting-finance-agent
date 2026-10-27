"""Expose persistent approved memory and skills through local filesystem routes."""

from pathlib import Path

from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from deepagents.backends.protocol import (
    BackendProtocol,
    DeleteResult,
    EditResult,
    FileUploadResponse,
    WriteResult,
)

from accounting_finance_agent.config import EXCEL_PROFILE, PROJECT_ROOT, Settings


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


def reference_roots(settings: Settings | None = None) -> dict[str, Path]:
    """Only selected procedural references are reachable in the benchmark."""
    if settings is not None and settings.profile == EXCEL_PROFILE:
        return {
            "/memories/": PROJECT_ROOT / "references" / "excel-benchmark" / "memory",
            "/skills/": PROJECT_ROOT / "references" / "excel-benchmark" / "skills",
            "/skills/file-delivery-validation/": SKILLS_ROOT / "file-delivery-validation",
            "/skills/csv-analysis/": SKILLS_ROOT / "csv-analysis",
            "/skills/financial-working-paper/": SKILLS_ROOT / "financial-working-paper",
        }
    return {"/memories/": MEMORY_ROOT, SKILLS_PATH: SKILLS_ROOT}


def knowledge_backend(execution_backend: BackendProtocol | None = None,
                      *, settings: Settings | None = None) -> CompositeBackend:
    """Keep approved files on the host; leave ordinary file operations on the default."""
    roots = reference_roots(settings)
    for folder in roots.values():
        if folder.is_symlink() or folder.is_junction():
            raise ValueError(f"Approved reference folders must not be links: {folder}")
        folder.mkdir(parents=True, exist_ok=True)
    routes = {route: ApprovedFilesBackend(root_dir=folder, virtual_mode=True)
              for route, folder in roots.items()}
    if settings is not None and settings.profile == EXCEL_PROFILE:
        routes = {
            "/memories/": routes["/memories/"],
            SKILLS_PATH: CompositeBackend(
                default=routes[SKILLS_PATH],
                routes={route.removeprefix("/skills"): backend
                        for route, backend in routes.items()
                        if route.startswith("/skills/") and route != SKILLS_PATH},
            ),
        }
    return CompositeBackend(
        default=execution_backend if execution_backend is not None else StateBackend(),
        routes=routes,
    )
