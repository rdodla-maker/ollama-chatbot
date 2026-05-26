from tools import (
    calculator_tool,
    pdf_search_tool,
    file_reader_tool,
    folder_scanner_tool
)

# Execute planned tasks
def execute_task(task):

    task_lower = task.lower()

    # Calculator
    if any(op in task for op in ["+", "-", "*", "/"]):

        return calculator_tool(task)

    # PDF Search
    if "pdf" in task_lower:

        return pdf_search_tool(task)

    # Read File
    if "read file" in task_lower:

        file_path = (
            task.split("read file")[-1]
            .strip()
        )

        return file_reader_tool(file_path)

    # Scan Folder
    if "scan folder" in task_lower:

        folder_path = (
            task.split("scan folder")[-1]
            .strip()
        )

        return folder_scanner_tool(folder_path)

    return "Task executed."