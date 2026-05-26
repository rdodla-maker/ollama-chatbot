"""
LangGraph ReAct agent with LLM tool calling.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

from core.config import settings
from core.logging_config import get_logger
from memory.store import memory_store
from planner import create_plan
from tools.registry import get_agent_tools

logger = get_logger("agent")

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        llm = ChatOllama(
            model=settings.ollama_model,
            temperature=0,
        )
        _graph = create_react_agent(llm, get_agent_tools())
        logger.info("LangGraph ReAct agent initialized")
    return _graph


def reset_graph() -> None:
    """Clear cached graph (e.g. after tool config change)."""
    global _graph
    _graph = None


def _build_messages(question: str, plan: str) -> list:
    memory_context = memory_store.get_context_for_query(question)
    system_prompt = f"""You are an autonomous AI engineering assistant with access to tools.
Use tools when they help answer accurately. Think step by step.
For file changes, use propose_file_edit — never claim a file was written without approval.

PAST MEMORY:
{memory_context}

EXECUTION PLAN:
{plan}
"""
    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=question),
    ]


def _extract_reasoning(messages: list) -> list[str]:
    steps: list[str] = []
    for msg in messages:
        if isinstance(msg, AIMessage):
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    name = tc.get("name", "tool")
                    args = tc.get("args", {})
                    steps.append(f"Action: {name}({args})")
            elif msg.content and len(messages) > 2:
                preview = str(msg.content)[:120].replace("\n", " ")
                if preview:
                    steps.append(f"Thought: {preview}...")
        elif isinstance(msg, ToolMessage):
            preview = str(msg.content)[:250].replace("\n", " ")
            steps.append(f"Observation: {preview}")
    return steps


def run_langgraph_agent(question: str) -> dict:
    """Run the ReAct agent loop with tools and memory."""
    plan = create_plan(question)

    reasoning_steps = [
        f"User asked: {question}",
        "Created execution plan.",
        "Running LangGraph ReAct agent with tool calling.",
    ]

    graph = _get_graph()
    result = graph.invoke(
        {"messages": _build_messages(question, plan)},
        config={"recursion_limit": settings.agent_max_iterations},
    )

    messages = result.get("messages", [])
    tool_steps = _extract_reasoning(messages)
    reasoning_steps.extend(tool_steps)

    final_message = messages[-1] if messages else None
    if isinstance(final_message, AIMessage):
        response = str(final_message.content)
    elif final_message is not None:
        response = str(getattr(final_message, "content", final_message))
    else:
        response = "No response generated."

    reasoning_steps.append("Agent completed.")
    memory_store.append(question, plan, response)

    return {
        "reasoning": reasoning_steps,
        "plan": plan,
        "response": response,
    }
