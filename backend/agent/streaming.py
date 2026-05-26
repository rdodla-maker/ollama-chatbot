"""
Stream agent execution events for SSE (/agent/stream).
"""

from collections.abc import Iterator

from langchain_core.messages import AIMessage, ToolMessage

from agent.graph import _build_messages, _extract_reasoning, _get_graph
from core.config import settings
from core.logging_config import get_logger
from memory.store import memory_store
from planner import create_plan

logger = get_logger("agent")


def stream_agent(question: str) -> Iterator[dict]:
    """
    Yield SSE-friendly event dicts:
      {type: plan|reasoning|token|done|error, ...}
    """
    try:
        plan = create_plan(question)
        yield {"type": "plan", "content": plan}
        yield {"type": "reasoning", "step": f"User asked: {question}"}
        yield {"type": "reasoning", "step": "Created execution plan."}
        yield {"type": "reasoning", "step": "Running LangGraph ReAct agent (streaming)."}

        graph = _get_graph()
        messages = _build_messages(question, plan)

        final_response = ""
        last_msg_count = 0
        all_reasoning: list[str] = []
        current: list = []

        for state in graph.stream(
            {"messages": messages},
            config={"recursion_limit": settings.agent_max_iterations},
            stream_mode="values",
        ):
            current = state.get("messages", [])
            if len(current) <= last_msg_count:
                continue

            new_msgs = current[last_msg_count:]
            last_msg_count = len(current)

            for msg in new_msgs:
                if isinstance(msg, AIMessage):
                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            step = f"Action: {tc.get('name', 'tool')}({tc.get('args', {})})"
                            all_reasoning.append(step)
                            yield {"type": "reasoning", "step": step}
                    elif msg.content:
                        text = str(msg.content)
                        if len(text) > len(final_response):
                            delta = text[len(final_response):]
                            final_response = text
                            if delta:
                                yield {"type": "token", "content": delta}
                elif isinstance(msg, ToolMessage):
                    step = f"Observation: {str(msg.content)[:250]}"
                    all_reasoning.append(step)
                    yield {"type": "reasoning", "step": step}

        if not final_response and last_msg_count:
            last = current[-1] if current else None
            if isinstance(last, AIMessage) and last.content:
                final_response = str(last.content)
                yield {"type": "token", "content": final_response}

        yield {"type": "reasoning", "step": "Agent completed."}
        memory_store.append(question, plan, final_response)

        yield {
            "type": "done",
            "response": final_response,
            "plan": plan,
            "reasoning": all_reasoning,
        }

    except Exception as exc:
        logger.exception("Agent stream failed")
        yield {"type": "error", "message": str(exc)}
