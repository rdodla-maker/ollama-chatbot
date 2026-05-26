"""
LangChain tool registry for LangGraph ReAct agent.
"""

from langchain_core.tools import tool

from core.config import settings
from tools.calculator import calculator_tool as _calculator
from tools.codebase_tools import analyze_repository_tool, codebase_search_tool
from tools.file_tools import file_reader_tool as _file_reader
from tools.file_tools import folder_scanner_tool as _folder_scanner
from tools.patch_tool import propose_file_edit_tool as _propose_edit
from tools.pdf_tools import pdf_search_tool as _pdf_search
from tools.shell_tool import run_command_tool as _run_command


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Use for arithmetic: +, -, *, /, %, **, parentheses."""
    return _calculator(expression)


@tool
def pdf_search(query: str) -> str:
    """Search uploaded PDF documents for relevant content."""
    return _pdf_search(query)


@tool
def read_file(file_path: str) -> str:
    """Read a text file inside the project. Provide a path relative to project root."""
    return _file_reader(file_path)


@tool
def scan_folder(folder_path: str) -> str:
    """List readable files under a project folder. Skips venv, node_modules, .git."""
    return _folder_scanner(folder_path)


@tool
def codebase_search(query: str) -> str:
    """Semantic search over indexed project source code (backend + frontend)."""
    return codebase_search_tool(query)


@tool
def analyze_repository() -> str:
    """Analyze repository structure, dependencies, and layout."""
    return analyze_repository_tool()


@tool
def propose_file_edit(file_path: str, new_content: str) -> str:
    """
    Propose a file edit for human approval. Does not write immediately.
    Use when suggesting code changes the user should review.
    """
    return _propose_edit(file_path, new_content)


@tool
def run_command(command: str) -> str:
    """
    Run a restricted shell command in the project directory.
    Allowed: pytest, python, pip, npm, git status/diff, dir, ls.
    Only available when ENABLE_SHELL_TOOL=true.
    """
    return _run_command(command)


def get_agent_tools() -> list:
    """All tools available to the LangGraph agent."""
    tools = [
        calculator,
        pdf_search,
        read_file,
        scan_folder,
        codebase_search,
        analyze_repository,
        propose_file_edit,
    ]
    if settings.enable_shell_tool:
        tools.append(run_command)
    return tools
