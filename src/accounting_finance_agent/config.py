"""Load local configuration without embedding credentials in application code."""

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigurationError(ValueError):
    """A required setting is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    model: str
    reasoning_effort: str
    tracing_enabled: bool
    langsmith_project: str
    sandbox_snapshot_id: str | None = None
    timezone: str = "America/Toronto"
    max_model_calls: int = 40
    max_tool_calls: int = 120
    run_seconds: int = 900
    model_timeout_seconds: int = 120
    tool_timeout_seconds: int = 120
    max_output_tokens: int = 16000
    sandbox_allowed_hosts: tuple[str, ...] = (
        "pypi.org:443", "files.pythonhosted.org:443", "www.sec.gov:443", "data.sec.gov:443",
    )


def positive_setting(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        if value <= 0:
            raise ValueError
        return value
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer.") from exc


def load_settings(*, require_sandbox: bool = False) -> Settings:
    """Load the checkout's .env; existing process settings take precedence."""
    load_dotenv(PROJECT_ROOT / ".env", override=False)

    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise ConfigurationError("Set OPENAI_API_KEY in .env before starting the agent.")

    if require_sandbox and not os.getenv("LANGSMITH_API_KEY", "").strip():
        raise ConfigurationError("Set LANGSMITH_API_KEY in .env to use --sandbox.")

    tracing = os.getenv("LANGSMITH_TRACING", "false").strip().lower() or "false"
    if tracing not in {"true", "false"}:
        raise ConfigurationError("LANGSMITH_TRACING must be true or false.")
    if tracing == "true" and not os.getenv("LANGSMITH_API_KEY", "").strip():
        raise ConfigurationError(
            "Set LANGSMITH_API_KEY in .env, or set LANGSMITH_TRACING=false."
        )

    reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "high").strip() or "high"
    if reasoning_effort not in {"low", "medium", "high"}:
        raise ConfigurationError("OPENAI_REASONING_EFFORT must be low, medium, or high.")

    project = os.getenv("LANGSMITH_PROJECT", "").strip() or "accounting-finance-agent"
    os.environ["LANGSMITH_PROJECT"] = project
    timezone_name = os.getenv("AGENT_TIMEZONE", "America/Toronto").strip()
    try:
        ZoneInfo(timezone_name)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ConfigurationError(f"Unknown AGENT_TIMEZONE: {timezone_name!r}") from exc
    hosts = tuple(host.strip() for host in os.getenv(
        "SANDBOX_ALLOWED_HOSTS", "pypi.org:443,files.pythonhosted.org:443,www.sec.gov:443,data.sec.gov:443"
    ).split(",") if host.strip())
    if not hosts:
        raise ConfigurationError("SANDBOX_ALLOWED_HOSTS must contain at least one allowed host.")

    return Settings(
        model=os.getenv("OPENAI_MODEL", "").strip() or "gpt-6-luna",
        reasoning_effort=reasoning_effort,
        tracing_enabled=tracing == "true",
        langsmith_project=project,
        sandbox_snapshot_id=os.getenv("SANDBOX_SNAPSHOT_ID", "").strip() or None,
        timezone=timezone_name,
        max_model_calls=positive_setting("AGENT_MAX_MODEL_CALLS", 40),
        max_tool_calls=positive_setting("AGENT_MAX_TOOL_CALLS", 120),
        run_seconds=positive_setting("AGENT_RUN_SECONDS", 900),
        model_timeout_seconds=positive_setting("AGENT_MODEL_TIMEOUT_SECONDS", 120),
        tool_timeout_seconds=positive_setting("AGENT_TOOL_TIMEOUT_SECONDS", 120),
        max_output_tokens=positive_setting("AGENT_MAX_OUTPUT_TOKENS", 16000),
        sandbox_allowed_hosts=hosts,
    )
