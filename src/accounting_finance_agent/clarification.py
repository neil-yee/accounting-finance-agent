"""Transport-neutral clarification requests backed by LangGraph interrupts."""

from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from langchain.agents.middleware import AgentMiddleware
from langgraph.types import interrupt


class ClarificationIsolationMiddleware(AgentMiddleware):
    """Prevent other tools from running in the same model turn as an interrupt."""

    def wrap_model_call(self, request, handler):
        response = handler(request)
        messages = [response] if isinstance(response, AIMessage) else response.result
        for message in messages:
            if isinstance(message, AIMessage):
                calls = message.tool_calls
                if len(calls) > 1 and any(call['name'] == 'ask_clarification' for call in calls):
                    raise ValueError('Clarification must be requested without parallel tool calls.')
        return response


@tool
def ask_clarification(question: str) -> str:
    """Pause the assignment and ask a person for information needed to proceed.

    Ask clearly for the information or decision needed, grouping related questions
    where practical. Use available context and make reasonable, reversible choices
    first; use this only when missing or conflicting information prevents a reliable
    result or a necessary decision is outside your authority. Do not invent facts.
    Do not combine this call with other tool calls in the same turn.
    """
    question = question.strip()
    if not question:
        raise ValueError("A clarification question is required.")
    answer = interrupt({"type": "clarification", "version": 1, "question": question})
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("A non-empty clarification response is required.")
    return answer.strip()


def pending_requests(snapshot):
    """Return the checkpoint's pending clarification IDs and payloads."""
    requests = []
    for item in snapshot.interrupts:
        value = item.value
        if not isinstance(value, dict) or value.get("type") != "clarification":
            raise ValueError("An unsupported interrupt is pending; inspect the checkpoint before continuing.")
        requests.append({"id": item.id, "type": value["type"],
                         "version": value.get("version"), "question": value.get("question", "")})
    return requests
