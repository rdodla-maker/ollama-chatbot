"""Stream agentic loop events for SSE consumers.

Yields dict events with types: 'plan', 'reasoning', 'observation', 'token', 'done'.
"""

from collections.abc import Iterator

from core.logging_config import get_logger
from core.config import settings
from agent.router import decide_tool
from langchain_ollama.llms import OllamaLLM
from memory.store import memory_store
from tools import (
    calculator_tool,
    file_reader_tool,
    folder_scanner_tool,
    pdf_search_tool,
)
from tools.codebase_tools import codebase_search_tool
from executor import execute_task

logger = get_logger("agent.stream")
llm = OllamaLLM(model=settings.ollama_model)


def stream_agent(question: str) -> Iterator[dict]:
    plan = f"Plan for: {question}"
    yield {"type": "plan", "content": plan}

    memory_context = memory_store.get_context_for_query(question)

    for step in range(settings.agent_max_iterations):
        routing = decide_tool(question)
        tool = routing.get("tool", "none")
        args = routing.get("args", {}) or {}

        yield {"type": "reasoning", "step": f"Step {step+1}: selected {tool}"}

        if tool == "none":
            yield {"type": "reasoning", "step": "No tool selected; finishing."}
            break

        try:
            if tool == "calculator":
                expr = args.get("expression") or question
                obs = calculator_tool(expr)
            elif tool == "pdf_search":
                q = args.get("query") or question
                obs = pdf_search_tool(q)
            elif tool == "file_read":
                path = args.get("path") or ""
                obs = file_reader_tool(path)
            elif tool == "folder_scan":
                path = args.get("path") or ""
                obs = folder_scanner_tool(path)
            elif tool == "code_search":
                q = args.get("query") or question
                obs = codebase_search_tool(q)
            elif tool == "execute":
                obs = execute_task(question)
            else:
                obs = f"Unknown tool: {tool}"
        except Exception as exc:
            obs = f"Tool error: {exc}"
            logger.exception("Tool error")

        yield {"type": "observation", "content": str(obs)}

        # Let the model decide to continue or finish
        moderator = llm.invoke(
            f"Decide to CONTINUE or FINISH for question: {question}\nObservation: {obs}\nMemory: {memory_context}"
        )

        if moderator.strip().upper().startswith("FINISH"):
            # produce final answer
            final = llm.invoke(f"Answer the question using observations:\n{obs}\nMemory:\n{memory_context}\nQuestion:\n{question}")
            # Stream final as token chunks (simple split)
            for i in range(0, len(final), 200):
                yield {"type": "token", "content": final[i:i+200]}
            yield {"type": "done", "response": final, "plan": plan}
            return

    # Max iterations reached
    final = llm.invoke(f"Max iterations reached; answer:\nQuestion: {question}\nObservations:\n{obs}")
    for i in range(0, len(final), 200):
        yield {"type": "token", "content": final[i:i+200]}
    yield {"type": "done", "response": final, "plan": plan}
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
