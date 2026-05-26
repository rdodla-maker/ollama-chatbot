from langchain_ollama.llms import OllamaLLM

from core.config import settings

llm = OllamaLLM(
    model=settings.ollama_model
)

# Create execution plan
def create_plan(task):

    prompt = f"""
You are an autonomous AI agent.

Break this task into clear execution steps.

Task:
{task}

Return concise numbered steps.
"""

    plan = llm.invoke(prompt)

    return plan