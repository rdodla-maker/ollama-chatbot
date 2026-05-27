"""LLM-based tool router: ask the LLM to select the most suitable tool and args.

This is a conservative router that prompts the model to return JSON with fields:
  {"tool": "calculator|pdf_search|file_read|folder_scan|code_search|execute|none",
   "args": { ... }}

If parsing fails, callers should fallback to legacy routing.
"""

import json
from typing import Any

from langchain_ollama.llms import OllamaLLM

from core.config import settings
from core.logging_config import get_logger

logger = get_logger("agent.router")

llm = OllamaLLM(model=settings.ollama_model)


def decide_tool(question: str) -> dict[str, Any]:
    """Ask the LLM to decide a tool and arguments for the given question.

    Returns a dict with keys 'tool' and 'args'. On error returns {'tool':'none','args':{}}
    """
    prompt = f"""
You are a tool selection assistant. Given a user request, choose the single best tool to handle it.

Respond with JSON only, no other text. The JSON shape:
{{"tool": "<tool-name>", "args": {{...}}}}

Allowed tools: calculator, pdf_search, file_read, folder_scan, code_search, execute, none

Examples:
User: "What is 12 * 8?"
Output: {{"tool":"calculator","args":{{"expression":"12 * 8"}}}}

User: "Search PDFs for references to async programming"
Output: {{"tool":"pdf_search","args":{{"query":"references to async programming"}}}}

User: "I want to scan folder backend/src"
Output: {{"tool":"folder_scan","args":{{"path":"backend/src"}}}}

Question: {question}
"""
    try:
        raw = llm.invoke(prompt)
        # Extract JSON substring if model returns extra text
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON found in model output")
        jtext = raw[start : end + 1]
        parsed = json.loads(jtext)
        tool = parsed.get("tool", "none")
        args = parsed.get("args", {}) or {}
        return {"tool": str(tool), "args": args}
    except Exception as exc:
        logger.warning("Tool routing failed: %s", exc)
        return {"tool": "none", "args": {}}
