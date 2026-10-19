"""Live transfer check: one real sandbox, small synthetic files, no LLM calls.

Run from the project root:
    uv run --locked python scripts/check_workspace_transfer.py
"""

import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shlex
from time import monotonic, sleep
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from dotenv import load_dotenv
from langsmith.sandbox import ResourceNotFoundError, SandboxClient

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.sandbox import sandbox_backend
from accounting_finance_agent import workspace


def tiny_workbook() -> bytes:
    """Build a small XLSX fixture using only the Python standard library."""
    entries = {
        "[Content_Types].xml": '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>''',
        "_rels/.rels": '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>''',
        "xl/workbook.xml": '''<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Transfer Test" sheetId="1" r:id="rId1"/></sheets>
</workbook>''',
        "xl/_rels/workbook.xml.rels": '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>''',
        "xl/worksheets/sheet1.xml": '''<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Transfer test</t></is></c><c r="B1"><v>42</v></c></row></sheetData>
</worksheet>''',
    }
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def hashes(root: Path) -> dict[str, str]:
    return {
        file.relative_to(root).as_posix(): sha256(file.read_bytes()).hexdigest()
        for file in sorted(root.rglob("*"))
        if file.is_file() and not any(
            part.startswith(".") for part in file.relative_to(root).parts
        )
    }


def check_equal(actual: object, expected: object, message: str) -> None:
    # Explicit checks also run when Python is started with -O.
    if actual != expected:
        raise RuntimeError(f"FAIL: {message}")
    print(f"PASS: {message}")


def confirm_sandbox_deleted(
    client: SandboxClient, name: str, *, timeout: float = 60
) -> None:
    """Poll read-only status until the resource is absent, with a bounded wait."""
    deadline = monotonic() + timeout
    previous_status = None
    while True:
        try:
            status = client.get_sandbox_status(name).status
        except ResourceNotFoundError:
            print(f"PASS: sandbox deletion confirmed by API: {name}")
            return
        # A successful DELETE request need not make subsequent reads return 404
        # immediately. Neither a retained record nor 'stopped' proves deletion.
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Sandbox deletion was not confirmed within {timeout:g} seconds: "
                f"{name} (last status: {status}). Check it in LangSmith or rerun "
                f"this script with --check-deletion {name}; that creates no sandbox."
            )
        if status != previous_status:
            print(f"Waiting for sandbox deletion: {name} | status: {status}")
            previous_status = status
        sleep(min(2, remaining))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-deletion", metavar="SANDBOX_NAME",
        help="Only check deletion of an existing sandbox; do not create one.",
    )
    args = parser.parse_args()
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    if not os.getenv("LANGSMITH_API_KEY", "").strip():
        raise SystemExit("Set LANGSMITH_API_KEY in .env before running this check.")

    if args.check_deletion:
        print("Read-only deletion check; no sandbox will be created or started.")
        with SandboxClient() as client:
            confirm_sandbox_deleted(client, args.check_deletion)
        return

    workspace.prepare_workspace()
    # Use an isolated shared workspace for this process. Normal working files
    # are untouched, and the actual production transfer functions still run.
    test_root = workspace.LOCAL_WORKSPACE / "transfer-tests" / uuid4().hex[:12]
    print("Live check: creates ONE real sandbox; no model calls or package installs.")
    print(f"Synthetic test files will remain at: {test_root}")
    with patch.object(workspace, "LOCAL_WORKSPACE", test_root):
        workspace.prepare_workspace()
        fixtures = {
            "notes/résumé with spaces.txt": "Synthetic transfer check: café, £, €\n".encode(),
            "sample.xlsx": tiny_workbook(),
            "nested/all_bytes.bin": bytes(range(256)) * 4,
            "conflict.txt": b"Original version.\n",
        }
        for relative, content in fixtures.items():
            target = test_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        expected_upload = hashes(test_root)

        script = """
from hashlib import sha256
import json
from pathlib import Path
source = Path('/workspace')
result = {}
for path in sorted(source.rglob('*')):
    if path.is_file():
        relative = path.relative_to(source)
        result[relative.as_posix()] = sha256(path.read_bytes()).hexdigest()
(source / 'notes/résumé with spaces.txt').write_bytes(b'Updated remotely.\\n')
(source / 'conflict.txt').write_bytes(b'Sandbox revision.\\n')
(source / 'nested/all_bytes.bin').unlink()
(source / 'created-in-sandbox.txt').write_bytes(b'Created remotely.\\n')
print(json.dumps(result))
"""
        with sandbox_backend() as backend:
            sandbox_name = backend.id
            response = backend.execute(f"python3 -c {shlex.quote(script)}", timeout=30)
            if response.exit_code != 0:
                raise RuntimeError(f"Remote copy command failed: {response.output}")
            check_equal(
                json.loads(response.output), expected_upload,
                "uploaded files match local SHA-256 hashes",
            )

            # Simulate a user editing the same working file while the agent runs.
            (test_root / "conflict.txt").write_bytes(b"Local revision.\n")

        # Leaving the context merges into this SAME folder and requests deletion.
        expected_workspace = {
            **expected_upload,
            "notes/résumé with spaces.txt": sha256(b"Updated remotely.\n").hexdigest(),
            "conflict.txt": sha256(b"Local revision.\n").hexdigest(),
            "created-in-sandbox.txt": sha256(b"Created remotely.\n").hexdigest(),
        }
        check_equal(hashes(test_root), expected_workspace, "shared workspace matches expected bytes")
        check_equal(
            (test_root / ".versions" / sandbox_name / "notes/résumé with spaces.txt").read_bytes(),
            fixtures["notes/résumé with spaces.txt"],
            "previous version preserved before replacement",
        )
        check_equal(
            (test_root / ".conflicts" / sandbox_name / "conflict.txt").read_bytes(),
            b"Sandbox revision.\n", "concurrent sandbox revision saved separately",
        )
        check_equal(
            (test_root / "nested/all_bytes.bin").read_bytes(),
            fixtures["nested/all_bytes.bin"], "sandbox deletion did not delete the local file",
        )
        with SandboxClient() as client:
            confirm_sandbox_deleted(client, sandbox_name)
        print(f"\nTRANSFER CHECK PASSED\nOpen the shared test workspace at: {test_root}")


if __name__ == "__main__":
    main()
