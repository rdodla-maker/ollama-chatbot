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

logger = get_logger("agent")

llm = OllamaLLM(model=settings.ollama_model)


def run_legacy_agent(question: str) -> dict:
    question_lower = question.lower()
    reasoning_steps = [f"User asked: {question}"]

    memory_context = memory_store.get_context_for_query(question)
    plan = create_plan(question)
    reasoning_steps.append("Created execution plan.")
    reasoning_steps.append(f"Memory context loaded ({len(memory_store.entries)} entries).")

    # Calculator
    if any(op in question for op in ["+", "-", "*", "/"]):
        reasoning_steps.append("Detected mathematical operation.")
        try:
            expression = question.replace("What is", "").strip()
            result = calculator_tool(expression)
            reasoning_steps.append("Used calculator tool.")
            memory_store.append(question, plan, result)
            return {"reasoning": reasoning_steps, "plan": plan, "response": result}
        except Exception as e:
            return {"reasoning": reasoning_steps, "plan": plan, "response": str(e)}

    if "pdf" in question_lower or "document" in question_lower:
        reasoning_steps.append("Detected PDF/document query.")
        results = pdf_search_tool(question)
        reasoning_steps.append("Used PDF search tool.")
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

    if "codebase" in question_lower or "code search" in question_lower:
        reasoning_steps.append("Detected codebase search.")
        results = codebase_search_tool(question)
        reasoning_steps.append("Used codebase search.")
        prompt = f"Answer using code search results.\n\n{results}\n\nQuestion: {question}"
        final_answer = llm.invoke(prompt)
        memory_store.append(question, plan, final_answer)
        return {"reasoning": reasoning_steps, "plan": plan, "response": final_answer}

    if "scan folder" in question_lower:
        reasoning_steps.append("Detected folder scanning request.")
        try:
            folder_path = question.split("scan folder")[-1].strip()
            files = folder_scanner_tool(folder_path)
            reasoning_steps.append("Scanned project folder.")
            memory_store.append(question, plan, files)
            return {"reasoning": reasoning_steps, "plan": plan, "response": files}
        except Exception as e:
            return {"reasoning": reasoning_steps, "plan": plan, "response": str(e)}

    if "read file" in question_lower:
        reasoning_steps.append("Detected file reading request.")
        try:
            file_path = question.split("read file")[-1].strip()
            file_content = file_reader_tool(file_path)
            reasoning_steps.append("Read requested file.")
            prompt = f"Explain this code clearly.\n\nCode:\n{file_content}"
            explanation = llm.invoke(prompt)
            reasoning_steps.append("Analyzed file content.")
            memory_store.append(question, plan, explanation)
            return {"reasoning": reasoning_steps, "plan": plan, "response": explanation}
        except Exception as e:
            return {"reasoning": reasoning_steps, "plan": plan, "response": str(e)}

    if "analyze project" in question_lower:
        reasoning_steps.append("Detected project analysis task.")
        try:
            from tools.codebase_tools import analyze_repository_tool
            analysis_data = analyze_repository_tool()
            prompt = f"""Analyze this software project.

{analysis_data}

Explain: 1) Architecture 2) Technologies 3) Purpose 4) Suggestions"""
            analysis = llm.invoke(prompt)
            reasoning_steps.append("Generated architecture analysis.")
            memory_store.append(question, plan, analysis)
            return {"reasoning": reasoning_steps, "plan": plan, "response": analysis}
        except Exception as e:
            return {"reasoning": reasoning_steps, "plan": plan, "response": str(e)}

    if any(k in question_lower for k in ("task", "execute", "workflow")):
        reasoning_steps.append("Detected autonomous workflow task.")
        try:
            execution_result = execute_task(question)
            reasoning_steps.append("Executed workflow task.")
            prompt = f"""Task: {question}
Plan: {plan}
Memory: {memory_context}
Result: {execution_result}
Provide final answer, suggestions, improvements."""
            final_response = llm.invoke(prompt)
            reasoning_steps.append("Generated workflow response.")
            memory_store.append(question, plan, final_response)
            return {"reasoning": reasoning_steps, "plan": plan, "response": final_response}
        except Exception as e:
            return {"reasoning": reasoning_steps, "plan": plan, "response": str(e)}

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
