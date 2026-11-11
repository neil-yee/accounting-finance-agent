"""Secret-free runtime manifests for comparing configurations and run evidence."""

from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import json
import os
import platform

from accounting_finance_agent.config import (
    EXCEL_PROFILE, EXCEL_RUN_BLOCKERS, EXCEL_SETTINGS, PROFILE_ENVIRONMENT_FIELDS,
    PROJECT_ROOT, Settings,
)
from accounting_finance_agent.knowledge import reference_roots


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def effective_configuration(settings: Settings) -> dict:
    """Record explicit settings and asset hashes, never raw environment/credentials.

    This describes application configuration. Provider acceptance, installed
    sandbox packages and enforcement require separate runtime evidence.
    """
    dependencies = {}
    for name in ("deepagents", "langchain", "langchain-core", "langchain-openai",
                 "langgraph", "langgraph-checkpoint-sqlite", "langsmith", "openai",
                 "python-dotenv", "tzdata", "langchain-quickjs"):
        try:
            dependencies[name] = version(name)
        except PackageNotFoundError:
            dependencies[name] = "not installed"

    assets = set((PROJECT_ROOT / "src" / "accounting_finance_agent").glob("*.py"))
    assets.update(PROJECT_ROOT / name for name in ("pyproject.toml", "uv.lock", "config/model-pricing.json", "environments/finance/excel-v1-release.json"))
    for root in reference_roots(settings).values():
        assets.update(root.rglob("*.md"))
        assets.update(root.rglob("*.py"))
    hashes = {}
    for path in sorted(assets):
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents
                                    if parent != PROJECT_ROOT):
            raise ValueError("Configuration assets must not be symlinks.")
        if path.is_file():
            hashes[path.relative_to(PROJECT_ROOT).as_posix()] = digest(path.read_bytes())

    benchmark = settings.profile == EXCEL_PROFILE
    sources = {
        field: (settings.profile if benchmark and field in EXCEL_SETTINGS
                else f"{name} (environment/.env)" if name in os.environ else "application default")
        for field, name in PROFILE_ENVIRONMENT_FIELDS.items()
    }
    for field, name in (("sandbox_snapshot_id", "SANDBOX_SNAPSHOT_ID"),
                        ("timezone", "AGENT_TIMEZONE"), ("langsmith_project", "LANGSMITH_PROJECT")):
        sources[field] = settings.profile if benchmark and field in EXCEL_SETTINGS else f"{name} (environment/.env or default)"
    record = {
        "schema_version": 1,
        "settings": asdict(settings),
        "setting_sources": sources,
        "profile_overrides_environment_names": sorted(
            name for field, name in PROFILE_ENVIRONMENT_FIELDS.items()
            if benchmark and field in EXCEL_SETTINGS and name in os.environ
        ),
        "python": platform.python_version(),
        "dependencies": dependencies,
        "asset_sha256": hashes,
        "reference_routes": {route: root.relative_to(PROJECT_ROOT).as_posix()
                             for route, root in reference_roots(settings).items()},
        "model_input_policy": ({"modalities": ["text", "image"],
                                "image_counting": "provider preflight per embedded image",
                                "direct_document_audio_video": False}
                               if benchmark else "provider defaults"),
        "execution_blockers": list(EXCEL_RUN_BLOCKERS) if benchmark else [],
        "verification": "Configured values and local asset identities; not a provider or behavior check.",
    }
    record["configuration_sha256"] = digest(json.dumps(record, sort_keys=True).encode())
    return record
