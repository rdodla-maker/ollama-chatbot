"""Agentic loop: Thought -> Action -> Observation -> Repeat.

This is a conservative, production-oriented implementation that:
- Uses the LLM to propose the next action (tool + args)
- Executes safe, pre-registered tools
- Records reasoning, actions, and observations
- Stops when the LLM signals completion or max iterations reached
"""

from datetime import datetime
from typing import Dict, List

from langchain_ollama.llms import OllamaLLM

from core.config import settings
from core.logging_config import get_logger
from memory.store import memory_store
from agent.router import decide_tool
from tools import (
    calculator_tool,
    file_reader_tool,
    folder_scanner_tool,
    pdf_search_tool,
)
from tools.codebase_tools import codebase_search_tool
from executor import execute_task

logger = get_logger("agent.loop")

llm = OllamaLLM(model=settings.ollama_model)


def _timestamp() -> str:
    return datetime.utcnow().isoformat() + "Z"


def run_agentic_loop(question: str) -> Dict:
    """Run the structured agent loop and return plan, reasoning, and response."""
    trace: List[str] = []
    observations: List[str] = []
    plan = f"Plan for: {question}"

    memory_context = memory_store.get_context_for_query(question)

    for step in range(settings.agent_max_iterations):
        # Ask LLM what to do next via the router prompt helper
        trace.append(f"Step {step+1}: Asking router for tool selection")
        routing = decide_tool(question)
        tool = routing.get("tool", "none")
        args = routing.get("args", {}) or {}

        trace.append(f"Tool selected: {tool} — args: {args}")

        if tool == "none":
            trace.append("No tool selected; ending loop.")
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
            logger.exception("Tool execution failed")

        observations.append(obs)
        trace.append(f"Observation: {str(obs)[:400]}")

        # Let the LLM decide whether to continue or finish by summarizing
        summary_prompt = f"""
You are an agent loop moderator. The user asked:
{question}

Memory context:
{memory_context}

Recent observation:
{obs}

Decide whether to continue with another tool call or finish and produce a final answer.
Respond with one line: CONTINUE or FINISH. If FINISH, follow with a brief final answer.
"""

        try:
            moderator = llm.invoke(summary_prompt)
        except Exception as exc:
            moderator = "FINISH: Unable to get decision from model."
            logger.warning("Moderator LLM failed: %s", exc)

        if moderator.strip().upper().startswith("FINISH"):
            # Extract text after FINISH:
            parts = moderator.split(":", 1)
            final_text = parts[1].strip() if len(parts) > 1 else ""
            if not final_text:
                # As fallback, ask LLM to produce a final answer using memory + observations
                final_prompt = f"""Answer the user's question using memory and observations.

User question:
{question}

Memory:
{memory_context}

Observations:
{observations}
"""
                final_text = llm.invoke(final_prompt)

            trace.append("Agent finished per moderator instruction.")
            memory_store.append(question, plan, final_text)
            return {"plan": plan, "reasoning": trace + observations, "response": final_text}

        # otherwise continue looping
        trace.append("Moderator decided to continue to next step.")

    # Max iterations reached — produce a best-effort final answer
    final_prompt = f"""Reached max iterations. Provide best-effort answer.

User question:
{question}

Memory:
{memory_context}

Observations:
{observations}
"""
    final_text = llm.invoke(final_prompt)
    memory_store.append(question, plan, final_text)
    return {"plan": plan, "reasoning": trace + observations, "response": final_text}
