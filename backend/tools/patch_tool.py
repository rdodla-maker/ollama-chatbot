"""Propose file edits that require human approval."""

from services.pending_changes import propose_file_edit


def propose_file_edit_tool(file_path: str, new_content: str) -> str:
    """
    Propose replacing a file's contents. Does NOT write until user approves.
    Use for code changes the user should review first.
    """
    return propose_file_edit(file_path, new_content)
