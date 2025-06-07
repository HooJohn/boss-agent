"""Tool for performing search on the local file system (the 'internal knowledge base')."""

import os
import mammoth
from typing import Any, Optional, List
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.tools.advanced_tools.pdf_tool import PdfTextExtractTool
from boss_agent.utils import WorkspaceManager

class InternalSearchTool(LLMTool):
    name = "internal_search"
    description = "Search for information within the company's internal knowledge base (local file system)."

    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
            "file_type_filter": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of file extensions to filter by (e.g., ['pdf', 'docx', 'txt']).",
            },
            "path_filter": {
                "type": "string",
                "description": "Optional subdirectory to limit the search to.",
            },
        },
        "required": ["query"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager
        self.pdf_extractor = PdfTextExtractTool(workspace_manager)

    def _read_file_content(self, file_path: str) -> str:
        """Read the content of a file, with support for pdf and docx."""
        try:
            if file_path.endswith(".pdf"):
                # Use the existing PDF extraction logic
                return self.pdf_extractor.run_impl({"path": file_path}).result
            elif file_path.endswith(".docx"):
                with open(file_path, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    return result.value
            elif file_path.endswith((".txt", ".md", ".html", ".csv", ".json")):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            else:
                # For other file types, we don't attempt to read the content
                return ""
        except Exception as e:
            return f"Error reading file {file_path}: {e}"

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[List[dict]] = None,
    ) -> ToolImplOutput:
        query = tool_input.get("query")
        file_type_filter = tool_input.get("file_type_filter")
        path_filter = tool_input.get("path_filter")

        if not query:
            return ToolImplOutput("", "Query is required.")

        search_path = self.workspace_manager.root
        if path_filter:
            # Ensure the path filter is a safe, relative path
            safe_path_filter = os.path.normpath(path_filter).lstrip('./\\')
            search_path = os.path.join(self.workspace_manager.root, safe_path_filter)
            if not os.path.isdir(search_path):
                return ToolImplOutput("", f"Directory not found: {search_path}")

        found_files = []
        for root, _, files in os.walk(search_path):
            for file in files:
                if file_type_filter:
                    if not any(file.endswith(f".{ext}") for ext in file_type_filter):
                        continue
                
                file_path = os.path.join(root, file)
                content = self._read_file_content(file_path)
                
                if query.lower() in content.lower():
                    # For simplicity, we return the path of the matching file.
                    # A more advanced implementation could return snippets.
                    relative_path = os.path.relpath(file_path, self.workspace_manager.root)
                    found_files.append(relative_path)

        if not found_files:
            return ToolImplOutput(f"No results found for '{query}'.", "Search completed.")

        results = "\n".join(found_files)
        return ToolImplOutput(f"Found results for '{query}' in the following files:\n{results}", "Search completed.")
