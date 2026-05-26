"""
Restricted command execution inside the project sandbox.

Uses subprocess without shell=True. Not a full Docker sandbox — enable only locally.
"""

import re
import shlex
import subprocess

from core.config import settings
from core.logging_config import get_logger
from core.security import get_allowed_root

logger = get_logger("tools")

# Commands allowed as first token (lowercase)
ALLOWED_ROOT_COMMANDS = {
    "pytest",
    "python",
    "pip",
    "npm",
    "npx",
    "dir",
    "ls",
    "git",
    "echo",
    "type",
    "cat",
}

# Blocked patterns anywhere in command string
BLOCKED_PATTERNS = [
    r"[|&;`$<>]",           # shell chaining / redirection
    r"\.\./",                # traversal in command string
    r"\brm\b", r"\bdel\b", r"\brmdir\b",
    r"\bformat\b", r"\bshutdown\b",
    r"\bcurl\b", r"\bwget\b", r"\bpowershell\b",
    r"\bInvoke-", r"\bStart-Process",
]


def _validate_command(command: str) -> list[str]:
    cmd = command.strip()
    if not cmd:
        raise ValueError("Empty command.")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.I):
            raise ValueError(f"Blocked pattern in command: {pattern}")

    try:
        parts = shlex.split(cmd, posix=False)
    except ValueError as exc:
        raise ValueError(f"Invalid command syntax: {exc}") from exc

    if not parts:
        raise ValueError("Empty command.")

    root_cmd = parts[0].lower()
    # Handle `python -m pytest` style
    if root_cmd == "python" and len(parts) >= 3 and parts[1] == "-m":
        root_cmd = parts[2].lower()

    if root_cmd not in ALLOWED_ROOT_COMMANDS:
        raise ValueError(
            f"Command '{parts[0]}' not allowed. "
            f"Permitted roots: {', '.join(sorted(ALLOWED_ROOT_COMMANDS))}"
        )

    return parts


def run_command_tool(command: str) -> str:
    """Run a restricted command in the project root directory."""
    if not settings.enable_shell_tool:
        return (
            "Shell tool is disabled. Set ENABLE_SHELL_TOOL=true in .env "
            "only on trusted local machines."
        )

    try:
        parts = _validate_command(command)
        cwd = str(get_allowed_root())

        result = subprocess.run(
            parts,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=settings.shell_timeout_seconds,
            shell=False,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        if not output:
            output = "(no output)"

        output = output[:8000]
        logger.info("Command finished exit=%s: %s", result.returncode, command[:80])
        return f"Exit code: {result.returncode}\n{output}"

    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {settings.shell_timeout_seconds}s"
    except Exception as e:
        logger.warning("Command failed: %s", e)
        return f"Error: {str(e)}"
