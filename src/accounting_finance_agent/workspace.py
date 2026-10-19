"""Copy the selected workspace to a sandbox and preserve new or changed files."""

from hashlib import sha256
from contextlib import contextmanager
from contextvars import ContextVar
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import shlex
from tempfile import NamedTemporaryFile

from langsmith.sandbox import Sandbox

from accounting_finance_agent.config import PROJECT_ROOT


LOCAL_WORKSPACE = PROJECT_ROOT / "workspace"
REMOTE_WORKSPACE = "/workspace"
_ACTIVE_WORKSPACE: ContextVar[Path | None] = ContextVar("finance_workspace", default=None)


def workspace_root() -> Path:
    return _ACTIVE_WORKSPACE.get() or LOCAL_WORKSPACE


def thread_workspace(thread_id: str) -> Path:
    from uuid import UUID
    key = str(UUID(thread_id))
    path = LOCAL_WORKSPACE / "threads" / key
    for folder in (LOCAL_WORKSPACE, LOCAL_WORKSPACE / "threads", path):
        if folder.is_symlink() or folder.is_junction():
            raise ValueError(f"Workspace must not contain directory links: {folder}")
    path.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def use_workspace(path: Path):
    token = _ACTIVE_WORKSPACE.set(path)
    try:
        prepare_workspace()
        yield
    finally:
        _ACTIVE_WORKSPACE.reset(token)


def workspace_manifest() -> dict[str, str]:
    """Hash eligible local files for run provenance and version-specific review."""
    root = workspace_root()
    result = {}
    for candidate in sorted(root.rglob("*")):
        relative = candidate.relative_to(root).as_posix()
        if not _included(PurePosixPath(relative)):
            continue
        path = _local_path(relative)
        if path.is_file():
            digest = sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            result[relative] = digest.hexdigest()
    return result


def prepare_workspace() -> None:
    """Create the selected local folder without following a directory link."""
    root = workspace_root()
    if root.is_symlink() or root.is_junction():
        raise ValueError(f"Workspace must not be a link: {root}")
    root.mkdir(parents=True, exist_ok=True)


def _included(relative: PurePosixPath) -> bool:
    # Histories/conflicts, credentials, caches, and old transfer-test artifacts
    # must not become inputs to the next normal agent run.
    return bool(relative.parts) and not (
        any(part.startswith(".") or part == "__pycache__" for part in relative.parts)
        or relative.parts[0] == "transfer-tests"
    )


def _local_path(relative: str) -> Path:
    path = PurePosixPath(relative)
    if (
        path.is_absolute()
        or not path.parts
        or ".." in path.parts
        or "\\" in relative
        or ":" in relative
        or any(ntpath.isreserved(part) for part in path.parts)
    ):
        raise ValueError(f"Unsafe workspace path: {relative!r}")
    current = workspace_root()
    for part in path.parts:
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise ValueError(f"Workspace links are not supported: {current}")
    if not current.resolve().is_relative_to(workspace_root().resolve()):
        raise ValueError(f"Path leaves the workspace: {relative!r}")
    return current


def _preserve(folder: str, run_name: str, relative: str, content: bytes) -> Path:
    target = _local_path(f"{folder}/{run_name}/{relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Permit an identical retry without overwriting a different saved version.
    if target.exists() and target.read_bytes() == content:
        return target
    with target.open("xb") as output:
        output.write(content)
    return target


def _replace(target: Path, content: bytes) -> None:
    """Complete the download before atomically replacing a working file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=target.parent, prefix=".download-", delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(content)
        except BaseException:
            output.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def upload_workspace(sandbox: Sandbox) -> dict[str, str]:
    """Upload working copies and record the bytes present at the start of a run."""
    prepare_workspace()
    baseline = {}
    for source in sorted(workspace_root().rglob("*")):
        relative = source.relative_to(workspace_root()).as_posix()
        if not _included(PurePosixPath(relative)):
            continue
        source = _local_path(relative)
        if not source.is_file():
            continue
        remote = f"{REMOTE_WORKSPACE}/{relative}"
        parent = str(PurePosixPath(remote).parent)
        result = sandbox.run(f"mkdir -p -- {shlex.quote(parent)}", timeout=30)
        if result.exit_code != 0:
            raise RuntimeError(f"Could not prepare workspace directory: {parent}")
        content = source.read_bytes()
        sandbox.write(remote, content)
        baseline[relative] = sha256(content).hexdigest()
    print(f"Workspace files uploaded: {len(baseline)} from {workspace_root()}")
    return baseline


def download_workspace(sandbox: Sandbox, run_name: str, baseline: dict[str, str]) -> dict:
    """Merge remote changes back, saving previous versions and local conflicts."""
    script = """
from hashlib import sha256
import json
import os
from pathlib import Path
root = Path('/workspace')
if root.is_symlink() or not root.is_dir():
    raise RuntimeError('Workspace directory is missing or is a link')
files = {}
for directory, dirs, names in os.walk(root, followlinks=False):
    dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d != '__pycache__'
                     and not (Path(directory) / d).is_symlink()
                     and not (Path(directory) == root and d == 'transfer-tests'))
    for name in sorted(names):
        path = Path(directory) / name
        if name.startswith('.') or path.is_symlink() or not path.is_file():
            continue
        digest = sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        files[path.relative_to(root).as_posix()] = digest.hexdigest()
print(json.dumps(files))
"""
    result = sandbox.run(f"python3 -c {shlex.quote(script)}", timeout=60)
    if result.exit_code != 0:
        raise RuntimeError("Could not list sandbox workspace files.")
    files = json.loads(result.stdout)
    if not isinstance(files, dict) or any(
        not isinstance(name, str) or not isinstance(digest, str)
        for name, digest in files.items()
    ):
        raise ValueError("Invalid sandbox workspace listing.")
    prepare_workspace()
    changed = conflicts = 0
    changed_files, conflict_files = {}, {}
    targets = set()
    for relative, digest in files.items():
        target = _local_path(relative)
        if not _included(PurePosixPath(relative)):
            continue
        # Prevent Linux names that collide when copied to a Windows filesystem.
        key = relative.casefold()
        if key in targets:
            raise ValueError(f"Case-colliding workspace filename: {relative!r}")
        targets.add(key)
        if digest == baseline.get(relative):
            continue  # Remote file unchanged: also leave any local edit intact.
        original = target.read_bytes() if target.is_file() else None
        local_digest = sha256(original).hexdigest() if original is not None else None
        if local_digest == digest:
            continue
        content = sandbox.read(f"{REMOTE_WORKSPACE}/{relative}")
        if sha256(content).hexdigest() != digest:
            raise RuntimeError(f"Sandbox file changed during download: {relative}")
        if local_digest != baseline.get(relative):
            saved = _preserve(".conflicts", run_name, relative, content)
            print(f"Local change kept; sandbox version saved for review: {saved}")
            conflicts += 1
            conflict_files[relative] = digest
            continue
        if original is not None:
            _preserve(".versions", run_name, relative, original)
        _replace(target, content)
        changed += 1
        changed_files[relative] = digest
    # Missing remote files are intentionally not deleted from the local workspace.
    print(
        f"Workspace downloaded: {changed} new/changed files, {conflicts} conflicts "
        f"saved for review in {workspace_root()}"
    )
    return {"remote_files": files, "changed_files": changed_files, "conflict_files": conflict_files}
