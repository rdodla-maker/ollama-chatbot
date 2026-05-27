"""Agent entry point — LangGraph with legacy fallback and streaming."""

from collections.abc import Iterator

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("agent")


def ask_agent(question: str) -> dict:
    """
    Main autonomous agent API.

    Uses LangGraph ReAct when enabled; falls back to legacy keyword router.
    """
    # Prefer LangGraph if enabled
    if settings.use_langgraph_agent:
        try:
            from agent.graph import run_langgraph_agent
            return run_langgraph_agent(question)
        except Exception as exc:
            logger.exception("LangGraph agent failed (%s), falling back", exc)

    # Next, use the agentic loop if enabled
    if settings.use_agentic_loop:
        try:
            from agent.loop import run_agentic_loop
            return run_agentic_loop(question)
        except Exception:
            logger.exception("Agentic loop failed, falling back to legacy")

    from agent.legacy import run_legacy_agent
    return run_legacy_agent(question)


def stream_agent_events(question: str) -> Iterator[dict]:
    """
    Stream agent events for SSE.

    Uses LangGraph streaming when enabled; otherwise yields legacy result once.
    """
    if settings.use_langgraph_agent:
        try:
            from agent.streaming import stream_agent
            yield from stream_agent(question)
            return
        except Exception as exc:
            logger.exception("LangGraph stream failed, using legacy: %s", exc)

        # If agentic loop is enabled, prefer its streaming implementation
        if settings.use_agentic_loop:
            try:
                from agent.streaming import stream_agent
                yield from stream_agent(question)
                return
            except Exception as exc:
                logger.exception("Agentic stream failed, falling back: %s", exc)

        result = ask_agent(question)
        yield {"type": "plan", "content": result.get("plan", "")}
        for step in result.get("reasoning", []):
            yield {"type": "reasoning", "step": step}
        yield {"type": "token", "content": result.get("response", "")}
        yield {
            "type": "done",
            "response": result.get("response", ""),
            "plan": result.get("plan", ""),
            "reasoning": result.get("reasoning", []),
        }
