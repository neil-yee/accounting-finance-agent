"""Build a default Deep Agent with the configured model."""

from deepagents import create_deep_agent
from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.memory import MemoryMiddleware
from langchain.agents.middleware import TodoListMiddleware
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.base import BaseCheckpointSaver

from accounting_finance_agent.config import Settings
from accounting_finance_agent.file_metadata import FileMetadataFilesystemMiddleware
from accounting_finance_agent.knowledge import (
    APPROVED_MEMORY_PROMPT,
    MEMORY_PATH,
    SKILLS_PATH,
    knowledge_backend,
)
from accounting_finance_agent.runtime import RunContext, RunControls


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
)


def build_agent(
    settings: Settings,
    *,
    backend: BackendProtocol | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    controls: RunControls | None = None,
):
    """Build the harness with persistent approved guidance and optional sandbox execution."""
    model = init_chat_model(
        settings.model,
        model_provider="openai",
        use_responses_api=True,
        reasoning={"effort": settings.reasoning_effort},
        timeout=settings.model_timeout_seconds,
        max_retries=2,
        max_tokens=settings.max_output_tokens,
    )
    routed_backend = knowledge_backend(backend)
    middleware = [
        FileMetadataFilesystemMiddleware(backend=routed_backend, controls=controls),
        TodoListMiddleware(),
        MemoryMiddleware(
            backend=routed_backend,
            sources=[MEMORY_PATH],
            system_prompt=APPROVED_MEMORY_PROMPT,
            add_cache_control=True,
        ),
    ]
    return create_deep_agent(
        model=model,
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
