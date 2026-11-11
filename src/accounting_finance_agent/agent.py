"""Build a default Deep Agent with the configured model."""

from hashlib import sha256
from threading import RLock

from deepagents import create_deep_agent
from deepagents.middleware.summarization import (
    DEEPAGENTS_DEFAULT_SUMMARY_PROMPT, compute_summarization_defaults,
    create_summarization_middleware,
)
from deepagents.profiles import (
    GeneralPurposeSubagentProfile, HarnessProfile, register_harness_profile,
)
from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.memory import MemoryMiddleware
from langchain.agents.middleware import TodoListMiddleware
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.base import BaseCheckpointSaver

from accounting_finance_agent.config import COLLAB_PROFILE, EXCEL_PROFILE, Settings
from accounting_finance_agent.clarification import ask_clarification, ClarificationIsolationMiddleware
from accounting_finance_agent.file_metadata import FileMetadataFilesystemMiddleware
from accounting_finance_agent.knowledge import (
    APPROVED_MEMORY_PROMPT,
    MEMORY_PATH,
    SKILLS_PATH,
    knowledge_backend,
)
from accounting_finance_agent.runtime import RunContext, RunControls


# Deep Agents 0.7.23 exposes model-keyed profile registration rather than a
# per-build profile argument. Serialize registration + assembly so two builds
# in this application cannot capture each other's delegation setting.
_HARNESS_BUILD_LOCK = RLock()


SANDBOX_INSTRUCTIONS = (
    "Your execution tools operate in a temporary remote Linux sandbox. "
    "Use python3 for Python and absolute paths under /workspace for working files. "
    "The user's local workspace folder is copied into /workspace at the start of this run. "
    "Read, create, revise, and organize files within this thread's working directory; "
    "there are no required input or output subfolders. Save deliverables and supporting "
    "scripts under /workspace. New and changed ordinary files are copied back locally "
    "before cleanup, with previous versions preserved. Sandbox deletions are not applied "
    "locally; moving a file may therefore leave the old local copy too. Hidden files, "
    "__pycache__, and the reserved transfer-tests folder are excluded from transfers. "
    "Other sandbox files are temporary and deleted after this run. "
    "The local project is not mounted; do not claim a local file exists unless it was transferred."
)

REFERENCE_INSTRUCTIONS = (
    "Approved shared guidance is available at /memories/AGENTS.md, and approved "
    "skill files under /skills/. Use file tools to access these read-only local routes; "
    "they are not mounted in the sandbox and cannot be opened by sandbox shell commands. "
    "When a skill provides code needed for execution, read it through file tools and "
    "copy the code into your sandbox working directory first. "
    "The owner maintains memory and skills."
    " Use the relevant validation skill for generated files. Report which checks actually "
    "ran, unresolved issues, and limitations; file creation alone is not validation."
    " Work independently within the task's scope. Use available sources and make "
    "reasonable, reversible choices when they do not materially affect the result; "
    "disclose relevant assumptions. Do not invent missing facts or explanations. "
    "Continue useful work that does not depend on an answer. Use ask_clarification "
    "when missing or conflicting information prevents a reliable result, or a needed "
    "decision is outside your authority. Group related questions in one request where "
    "practical. Call the clarification tool on its own, not in parallel with other "
    "tools. Subagents should report missing information to the main agent, which asks "
    "the person. A clarification is not authorization for an otherwise unapproved action."
)


def _build_agent(
    settings: Settings,
    *,
    backend: BackendProtocol | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    controls: RunControls | None = None,
):
    """Build the harness with persistent approved guidance and optional sandbox execution."""
    model_options = {}
    if settings.profile == EXCEL_PROFILE:
        if controls is None:
            raise ValueError("The benchmark requires shared run controls.")
        from accounting_finance_agent.budget import BudgetClient, DisabledAsyncClient
        client = BudgetClient(controls)
        controls.api_client = client
        model_options = {"http_client": client, "http_async_client": DisabledAsyncClient(), "disable_streaming": True,
                         "store": False, "http_socket_options": ()}
    model = init_chat_model(
        settings.model,
        model_provider="openai",
        use_responses_api=True,
        reasoning={"effort": settings.reasoning_effort},
        timeout=settings.model_timeout_seconds,
        max_retries=settings.sdk_max_retries,
        max_tokens=settings.max_output_tokens,
        **model_options,
        **({"service_tier": settings.service_tier} if settings.service_tier else {}),
    )
    register_harness_profile(
        f"openai:{settings.model}",
        HarnessProfile(general_purpose_subagent=GeneralPurposeSubagentProfile(
            enabled=settings.delegation_enabled and settings.profile != COLLAB_PROFILE,
        )),
    )
    routed_backend = knowledge_backend(backend, settings=settings)
    middleware = [
        ClarificationIsolationMiddleware(),
        FileMetadataFilesystemMiddleware(backend=routed_backend, controls=controls),
        TodoListMiddleware(),
        MemoryMiddleware(
            backend=routed_backend,
            sources=[MEMORY_PATH],
            system_prompt=APPROVED_MEMORY_PROMPT,
            add_cache_control=True,
        ),
    ]
    if settings.dynamic_subagents_enabled and settings.delegation_enabled:
        from langchain_quickjs import CodeInterpreterMiddleware
        # Opt-in local capability. PTC is disabled; JavaScript is scoped to a
        # single call. Subagent calls share the normal model-call budget, but
        # task() bridge dispatches do not pass the parent tool middleware.
        middleware.append(CodeInterpreterMiddleware(mode="call", max_subagent_concurrency=4,
                                                    timeout=10, ptc=None))
    if settings.profile == EXCEL_PROFILE:
        # Pinned adapter: BudgetClient owns retries, including summarization.
        # Avoid six transport attempts multiplied by three framework attempts.
        summarization = create_summarization_middleware(model, routed_backend)
        helper = getattr(summarization, "_lc_helper", None)
        if helper is None or not hasattr(helper, "_summary_model"):
            raise RuntimeError("Pinned summarization retry adapter needs review.")
        helper._summary_model = model
        middleware.append(summarization)
    subagents = None
    if settings.profile == COLLAB_PROFILE:
        from accounting_finance_agent.collaboration import PeerMailbox, reviewer_specs
        subagents = reviewer_specs(PeerMailbox(controls), routed_backend, controls)
    graph = create_deep_agent(
        model=model,
        tools=[ask_clarification],
        subagents=subagents,
        middleware=middleware,
        backend=routed_backend,
        system_prompt=(
            f"{REFERENCE_INSTRUCTIONS}\n\n{SANDBOX_INSTRUCTIONS}"
            if backend is not None else REFERENCE_INSTRUCTIONS
        ),
        memory=[MEMORY_PATH],
        skills=[SKILLS_PATH],
        checkpointer=checkpointer,
        context_schema=RunContext,
    )

    if controls is not None:
        controls.log.event(
            controls.context.run_id, "harness_configuration",
            delegation_enabled=settings.delegation_enabled,
            dynamic_subagents_enabled=settings.dynamic_subagents_enabled,
            explicit_subagents=[s['name'] for s in subagents] if subagents else [],
            compaction={
                "implementation": "deepagents.middleware.summarization.create_summarization_middleware",
                "defaults": compute_summarization_defaults(model),
                "summary_prompt_sha256": sha256(DEEPAGENTS_DEFAULT_SUMMARY_PROMPT.encode()).hexdigest(),
                "summarizer_model": settings.model,
                "model_max_input_tokens": (model.profile or {}).get("max_input_tokens"),
                "trim_tokens_to_summarize": None,
                "custom_summary_prompt": False,
                "retry_owner": "BudgetClient; no framework summary retries" if settings.profile == EXCEL_PROFILE else "framework defaults",
                "usage_accounting": "HTTP attempt ledger" if settings.profile == EXCEL_PROFILE else "logical calls only",
            },
        )
    return graph


def build_agent(
    settings: Settings,
    *,
    backend: BackendProtocol | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    controls: RunControls | None = None,
):
    """Compile one graph using an explicit, serialized delegation policy."""
    with _HARNESS_BUILD_LOCK:
        return _build_agent(settings, backend=backend, checkpointer=checkpointer, controls=controls)
