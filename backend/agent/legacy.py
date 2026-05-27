"""
Legacy keyword-based agent (Wave 1) — used as fallback when LangGraph fails.
"""

from langchain_ollama.llms import OllamaLLM

from core.config import settings
from core.logging_config import get_logger
from memory.store import memory_store
from planner import create_plan
from executor import execute_task
from tools import (
    calculator_tool,
    file_reader_tool,
    folder_scanner_tool,
    pdf_search_tool,
)
from tools.codebase_tools import codebase_search_tool
from agent.router import decide_tool

logger = get_logger("agent")

llm = OllamaLLM(model=settings.ollama_model)


def run_legacy_agent(question: str) -> dict:
    question_lower = question.lower()
    reasoning_steps = [f"User asked: {question}"]

    memory_context = memory_store.get_context_for_query(question)
    plan = create_plan(question)
    reasoning_steps.append("Created execution plan.")
    reasoning_steps.append(f"Memory context loaded ({len(memory_store.entries)} entries).")

    # Use LLM-based routing to pick a tool (fallback to keyword rules on failure)
    routing = decide_tool(question)
    tool = routing.get("tool", "none")
    args = routing.get("args", {}) or {}

    try:
        if tool == "calculator":
            expr = args.get("expression") or question
            reasoning_steps.append("Selected calculator via LLM router.")
            result = calculator_tool(expr)
            memory_store.append(question, plan, result)
            return {"reasoning": reasoning_steps, "plan": plan, "response": result}

        if tool == "pdf_search":
            q = args.get("query") or question
            reasoning_steps.append("Selected PDF search via LLM router.")
            results = pdf_search_tool(q)
            prompt = f"""Answer using PDF results and memory.

Memory:
{memory_context}

PDF Results:
{results}

Question:
{question}"""
            final_answer = llm.invoke(prompt)
            memory_store.append(question, plan, final_answer)
            return {"reasoning": reasoning_steps, "plan": plan, "response": final_answer}

        if tool == "code_search":
            q = args.get("query") or question
            reasoning_steps.append("Selected codebase search via LLM router.")
            results = codebase_search_tool(q)
            prompt = f"Answer using code search results.\n\n{results}\n\nQuestion: {question}"
            final_answer = llm.invoke(prompt)
            memory_store.append(question, plan, final_answer)
            return {"reasoning": reasoning_steps, "plan": plan, "response": final_answer}

        if tool == "folder_scan":
            path = args.get("path") or question
            reasoning_steps.append("Selected folder scan via LLM router.")
            files = folder_scanner_tool(path)
            memory_store.append(question, plan, files)
            return {"reasoning": reasoning_steps, "plan": plan, "response": files}

        if tool == "file_read":
            path = args.get("path") or question
            reasoning_steps.append("Selected file read via LLM router.")
            file_content = file_reader_tool(path)
            prompt = f"Explain this code clearly.\n\nCode:\n{file_content}"
            explanation = llm.invoke(prompt)
            memory_store.append(question, plan, explanation)
            return {"reasoning": reasoning_steps, "plan": plan, "response": explanation}

        if tool == "execute":
            reasoning_steps.append("Selected execute via LLM router.")
            execution_result = execute_task(question)
            prompt = f"""Task: {question}
Plan: {plan}
Memory: {memory_context}
Result: {execution_result}
Provide final answer, suggestions, improvements."""
            final_response = llm.invoke(prompt)
            memory_store.append(question, plan, final_response)
            return {"reasoning": reasoning_steps, "plan": plan, "response": final_response}

    except Exception as e:
        reasoning_steps.append(f"Tool execution failed: {e}")
        logger.exception("Tool execution error")

    # Fallback: continue with general AI reasoning

    reasoning_steps.append("Using general AI reasoning.")
    prompt = f"""You are an autonomous AI coding assistant.

Memory:
{memory_context}

Question:
{question}

Think step-by-step before answering."""
    final_answer = llm.invoke(prompt)
    reasoning_steps.append("Generated AI response.")
    memory_store.append(question, plan, final_answer)
    return {"reasoning": reasoning_steps, "plan": plan, "response": final_answer}
