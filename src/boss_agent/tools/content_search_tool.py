"""Tool for performing content search on the local file system."""

import os
from typing import Any, Optional, Dict
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.llm.message_history import MessageHistory
from boss_agent.utils import WorkspaceManager
from boss_agent.utils.file_reader import read_file_content

class ContentSearchTool(LLMTool):
    name = "content_search"
    description = "Recursively searches for a query string within the content of files in the knowledge base."

    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query for content search.",
            },
            "path_filter": {
                "type": "string",
                "description": "Subdirectory to limit the search to. Defaults to the knowledge base root.",
                "default": ".",
            },
            "file_type_filter": {
                "type": "array",
                "items": {"type": "string"},
                "description": "A list of file extensions to include in the search (e.g., ['csv', 'pdf']).",
            }
        },
        "required": ["query"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        query = tool_input.get("query")
        path_filter = tool_input.get("path_filter", ".")
        
        if not query:
            return ToolImplOutput("", "Error: 'query' parameter is required for content search.")

        # --- Path Sanitization ---
        safe_path_filter = os.path.normpath(os.path.join('/', path_filter)).lstrip('/\\')
        if ".." in safe_path_filter.split(os.sep):
            return ToolImplOutput("", "Error: Directory traversal is not allowed.")

        # --- Define Search Paths ---
        kb_path = os.path.join(self.workspace_manager.root, safe_path_filter)
        session_path = os.path.join(self.workspace_manager.session_workspace, safe_path_filter)

        # --- Validate Path Existence ---
        if not os.path.isdir(kb_path) and not os.path.isdir(session_path):
            return ToolImplOutput("", f"Error: Directory '{path_filter}' not found.")

        # --- Search file content ---
        file_type_filter = tool_input.get("file_type_filter")
        found_files: Dict[str, str] = {}

        for base_path in [kb_path, session_path]:
            if not os.path.isdir(base_path):
                continue

            for root, _, files in os.walk(base_path):
                for file in files:
                    if file_type_filter and not any(file.endswith(f".{ext}") for ext in file_type_filter):
                        continue
                    
                    file_path = os.path.join(root, file)
                    content = read_file_content(file_path, self.workspace_manager)
                    
                    if query.lower() in content.lower():
                        relative_to_filter = os.path.relpath(file_path, base_path)
                        display_path = os.path.join(path_filter, relative_to_filter)
                        found_files[display_path] = file_path

        if not found_files:
            return ToolImplOutput(f"No results found for '{query}'.", "Search completed.")

        results = "\n".join(sorted(found_files.keys()))
        return ToolImplOutput(f"Found results for '{query}' in the following files:\n{results}", "Search completed.")
