"""Load local configuration without embedding credentials in application code."""

import os
from dataclasses import dataclass, replace
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

    profile: str = "local"
    delegation_enabled: bool = True
    service_tier: str | None = None
    sdk_max_retries: int = 2


# Version this named baseline whenever a setting changes. Runtime evidence must
# distinguish these requested values from actual enforcement/provider behavior.
EXCEL_PROFILE = "excel-benchmark-v1"
EXCEL_SETTINGS = {
    "model": "gpt-6-luna",
    "reasoning_effort": "high",
    "tracing_enabled": True,
    "max_model_calls": 20,
    "max_tool_calls": 40,
    "run_seconds": 600,
    "model_timeout_seconds": 180,
    "tool_timeout_seconds": 120,
    "max_output_tokens": 32000,
    "delegation_enabled": False,
    # OpenAI calls its Standard service tier "default" in the API.
    "service_tier": "default",
    # Disable hidden SDK retries; the shared retry controller is still to build.
    "sdk_max_retries": 0,
    "sandbox_allowed_hosts": (),
}
PROFILE_ENVIRONMENT_FIELDS = {
    "model": "OPENAI_MODEL", "reasoning_effort": "OPENAI_REASONING_EFFORT",
    "tracing_enabled": "LANGSMITH_TRACING", "max_model_calls": "AGENT_MAX_MODEL_CALLS",
    "max_tool_calls": "AGENT_MAX_TOOL_CALLS", "run_seconds": "AGENT_RUN_SECONDS",
    "model_timeout_seconds": "AGENT_MODEL_TIMEOUT_SECONDS",
    "tool_timeout_seconds": "AGENT_TOOL_TIMEOUT_SECONDS",
    "max_output_tokens": "AGENT_MAX_OUTPUT_TOKENS", "sandbox_allowed_hosts": "SANDBOX_ALLOWED_HOSTS",
}

# This is an implementation gate, not an operator waiver. Remove entries only
# when the linked build requirements are implemented and assessed.
EXCEL_RUN_BLOCKERS = (
    "BUILD-06/07: shared API cost reservation, attempt accounting, five-retry policy and hard deadlines",
    "BUILD-03/04: frozen recalculation image and enforced sandbox network isolation",
    "BUILD-05/08: milestone preservation, transfer limits and complete usage/configuration evidence",
    "BUILD-04/09: independent Excel grader and required-output/recalculation gates",
)


def require_runnable_profile(settings: Settings) -> None:
    if settings.profile == EXCEL_PROFILE and EXCEL_RUN_BLOCKERS:
        raise ConfigurationError(
            "The Excel benchmark profile is staged, not runnable yet. "
            "Inspect it with --show-config. Outstanding work: " + "; ".join(EXCEL_RUN_BLOCKERS)
        )


def positive_setting(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        if value <= 0:
            raise ValueError
        return value
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer.") from exc


def load_settings(*, require_sandbox: bool = False, profile: str = "local",
                  validate_credentials: bool = True) -> Settings:
    """Load local settings; the named trial baseline overrides its fixed fields."""
    if profile not in {"local", EXCEL_PROFILE}:
        raise ConfigurationError(f"Unknown runtime profile: {profile}")
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    benchmark = profile == EXCEL_PROFILE

    def limit(field: str, environment_name: str, default: int) -> int:
        return EXCEL_SETTINGS[field] if benchmark else positive_setting(environment_name, default)

    if validate_credentials and not os.getenv("OPENAI_API_KEY", "").strip():
        raise ConfigurationError("Set OPENAI_API_KEY in .env before starting the agent.")

    if validate_credentials and require_sandbox and not os.getenv("LANGSMITH_API_KEY", "").strip():
        raise ConfigurationError("Set LANGSMITH_API_KEY in .env to use --sandbox.")

    tracing = "true" if benchmark else (os.getenv("LANGSMITH_TRACING", "false").strip().lower() or "false")
    if tracing not in {"true", "false"}:
        raise ConfigurationError("LANGSMITH_TRACING must be true or false.")
    if validate_credentials and tracing == "true" and not os.getenv("LANGSMITH_API_KEY", "").strip():
        raise ConfigurationError(
            "Set LANGSMITH_API_KEY in .env, or set LANGSMITH_TRACING=false."
        )

    reasoning_effort = "high" if benchmark else (os.getenv("OPENAI_REASONING_EFFORT", "high").strip() or "high")
    if reasoning_effort not in {"low", "medium", "high"}:
        raise ConfigurationError("OPENAI_REASONING_EFFORT must be low, medium, or high.")

    project = os.getenv("LANGSMITH_PROJECT", "").strip() or "accounting-finance-agent"
    os.environ["LANGSMITH_PROJECT"] = project
    if benchmark:
        os.environ["LANGSMITH_TRACING"] = "true"
    timezone_name = os.getenv("AGENT_TIMEZONE", "America/Toronto").strip()
    try:
        ZoneInfo(timezone_name)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ConfigurationError(f"Unknown AGENT_TIMEZONE: {timezone_name!r}") from exc
    hosts = tuple(host.strip() for host in os.getenv(
        "SANDBOX_ALLOWED_HOSTS", "pypi.org:443,files.pythonhosted.org:443,www.sec.gov:443,data.sec.gov:443"
    ).split(",") if host.strip())
    if not hosts and not benchmark:
        raise ConfigurationError("SANDBOX_ALLOWED_HOSTS must contain at least one allowed host.")

    settings = Settings(
        model=os.getenv("OPENAI_MODEL", "").strip() or "gpt-6-luna",
        reasoning_effort=reasoning_effort,
        tracing_enabled=tracing == "true",
        langsmith_project=project,
        sandbox_snapshot_id=os.getenv("SANDBOX_SNAPSHOT_ID", "").strip() or None,
        timezone=timezone_name,
        max_model_calls=limit("max_model_calls", "AGENT_MAX_MODEL_CALLS", 40),
        max_tool_calls=limit("max_tool_calls", "AGENT_MAX_TOOL_CALLS", 120),
        run_seconds=limit("run_seconds", "AGENT_RUN_SECONDS", 900),
        model_timeout_seconds=limit("model_timeout_seconds", "AGENT_MODEL_TIMEOUT_SECONDS", 120),
        tool_timeout_seconds=limit("tool_timeout_seconds", "AGENT_TOOL_TIMEOUT_SECONDS", 120),
        max_output_tokens=limit("max_output_tokens", "AGENT_MAX_OUTPUT_TOKENS", 16000),
        sandbox_allowed_hosts=hosts,
    )

    return replace(settings, profile=profile, **EXCEL_SETTINGS) if benchmark else settings
