"""Build a reusable environment in LangSmith; no agent or model calls.

Run: uv run --locked python scripts/build_sandbox_snapshot.py --activate
"""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
from time import monotonic, sleep
from uuid import uuid4

from dotenv import load_dotenv, set_key
from langsmith.sandbox import ResourceNotFoundError, SandboxClient
from accounting_finance_agent.provider import sandbox_client

from accounting_finance_agent.config import PROJECT_ROOT
from accounting_finance_agent.sandbox import (
    SANDBOX_DELETE_AFTER_STOP_SECONDS,
    SANDBOX_IDLE_TTL_SECONDS,
    SANDBOX_MEMORY_BYTES,
    SANDBOX_VCPUS,
)


ENVIRONMENT = PROJECT_ROOT / "environments" / "finance"
INVENTORY_COMMAND = "python3 -c " + shlex.quote(
    "import json,sys,subprocess; "
    "print(json.dumps({'python':sys.version.split()[0], "
    "'executable':sys.executable, 'packages':json.loads(subprocess.check_output("
    "[sys.executable,'-m','pip','list','--format=json','--disable-pip-version-check'],"
    "text=True))}))"
)


def run(sandbox, command: str, *, timeout: int = 60) -> str:
    result = sandbox.run(command, timeout=timeout)
    if result.exit_code != 0:
        raise RuntimeError(f"Environment preparation failed: {result.stderr}\n{result.stdout}")
    return result.stdout


def delete_builder(client: SandboxClient, name: str) -> None:
    try:
        client.delete_sandbox(name)
    except ResourceNotFoundError:
        pass
    deadline = monotonic() + 60
    while True:
        try:
            status = client.get_sandbox_status(name).status
        except ResourceNotFoundError:
            print(f"Builder deletion confirmed by API: {name}", flush=True)
            return
        if monotonic() >= deadline:
            raise RuntimeError(f"Check builder cleanup in LangSmith: {name} ({status})")
        sleep(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--activate", action="store_true", help="Select the built snapshot in local .env.")
    parser.add_argument("--base-snapshot", help="Override the recipe's base with an immutable snapshot ID.")
    parser.add_argument("--tag", help="Release tag override, useful for a CI commit/run identifier.")
    args = parser.parse_args()
    process_snapshot = os.getenv("SANDBOX_SNAPSHOT_ID", "").strip()
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    if not os.getenv("LANGSMITH_API_KEY", "").strip():
        parser.error("Set LANGSMITH_API_KEY before building a snapshot.")
    if args.activate and process_snapshot:
        parser.error("Unset process SANDBOX_SNAPSHOT_ID before --activate; it would override .env.")

    recipe_bytes = (ENVIRONMENT / "snapshot.json").read_bytes()
    recipe = json.loads(recipe_bytes)
    release_tag = args.tag or recipe["tag"]
    requirements = (ENVIRONMENT / "requirements.txt").read_bytes()
    has_extras = any(line.strip() and not line.lstrip().startswith("#")
                     for line in requirements.decode("utf-8").splitlines())
    name = f"finance-env-build-{uuid4().hex[:12]}"
    print("Creates one temporary builder; no model calls or task-file uploads.", flush=True)
    print(f"Builder: {name} | {SANDBOX_VCPUS} vCPU | {SANDBOX_MEMORY_BYTES / 1024**3:g} GiB RAM", flush=True)
    with sandbox_client() as client:
        base = client.get_snapshot(args.base_snapshot or recipe["base_snapshot"])
        if base.status != "ready":
            raise RuntimeError(f"Base snapshot is not ready: {base.id} ({base.status})")
        print(f"Resolved base snapshot: {base.id}", flush=True)
        try:
            client.create_sandbox(
                name=name, snapshot_id=base.id, wait_for_ready=False,
                vcpus=SANDBOX_VCPUS, mem_bytes=SANDBOX_MEMORY_BYTES,
                idle_ttl_seconds=SANDBOX_IDLE_TTL_SECONDS,
                delete_after_stop_seconds=SANDBOX_DELETE_AFTER_STOP_SECONDS,
            )
            sandbox = client.wait_for_sandbox(name, timeout=60)
            for command in recipe.get("prepare_commands", []):
                print(run(sandbox, command, timeout=240), flush=True)
            capture_config = {}
            if has_extras:
                # Keep the base's system packages; install extras in a separate venv.
                run(sandbox, "python3 -m venv --system-site-packages /opt/finance-python")
                sandbox.write("/tmp/finance-requirements.txt", requirements)
                run(sandbox, "/opt/finance-python/bin/python -m pip install --disable-pip-version-check "
                    "-r /tmp/finance-requirements.txt", timeout=240)
                base_path = run(sandbox, "printf '%s' \"$PATH\"").strip()
                capture_config["run_config"] = {"env_vars": {
                    "PATH": "/opt/finance-python/bin:" + base_path,
                    "VIRTUAL_ENV": "/opt/finance-python",
                }}
                inventory_command = INVENTORY_COMMAND.replace("python3 -c", "/opt/finance-python/bin/python -c", 1)
            else:
                print("No extra requirements: preserving the base libraries unchanged.", flush=True)
                inventory_command = INVENTORY_COMMAND
            inventory = json.loads(run(sandbox, inventory_command))
            print(f"Capturing {recipe['name']}:{release_tag} ...", flush=True)
            snapshot = client.capture_snapshot(
                name, recipe["name"], tag=release_tag, timeout=240, **capture_config,
            )
            manifest = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "git_commit": os.getenv("GITHUB_SHA"), "release_tag": release_tag,
                "snapshot": asdict(snapshot), "base_snapshot_id": base.id,
                "recipe_sha256": sha256(recipe_bytes).hexdigest(),
                "requirements_sha256": sha256(requirements).hexdigest(),
                "inventory": inventory,
                "system_packages": run(sandbox, "dpkg-query -W libreoffice-calc poppler-utils fonts-liberation"),
                "compute": {"vcpus": SANDBOX_VCPUS, "memory_bytes": SANDBOX_MEMORY_BYTES},
            }
            manifest_path = PROJECT_ROOT / ".state" / "snapshots" / f"{snapshot.id}.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            print(f"Snapshot ready: {snapshot.id}\nBuild record: {manifest_path}", flush=True)
            if output_file := os.getenv("GITHUB_OUTPUT"):
                with Path(output_file).open("a", encoding="utf-8") as output:
                    output.write(f"snapshot_id={snapshot.id}\n")
                    output.write(f"manifest={manifest_path.relative_to(PROJECT_ROOT).as_posix()}\n")
        finally:
            delete_builder(client, name)

    if args.activate:
        set_key(str(PROJECT_ROOT / ".env"), "SANDBOX_SNAPSHOT_ID", snapshot.id)
        print("Selected snapshot in .env. Restart the agent to use it.", flush=True)
    else:
        print(f"Select this release with SANDBOX_SNAPSHOT_ID={snapshot.id}", flush=True)


if __name__ == "__main__":
    main()
