"""Tool for writing content to a file."""

import os
from typing import Any, Optional, List
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.utils.workspace_manager import WorkspaceManager

class WriteFileTool(LLMTool):
    name = "write_to_file"
    description = "Writes content to a specified file. If the file exists, it will be overwritten. If it does not exist, it will be created."

    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file to be written to. The path should be relative to the workspace root.",
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file.",
            },
        },
        "required": ["file_path", "content"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager

    def _get_full_safe_path(self, file_path: str) -> Optional[str]:
        """Get the full, safe path to a file within the session workspace."""
        # Prevent path traversal attacks
        safe_path = os.path.normpath(os.path.join('/', file_path)).lstrip('/\\')
        if ".." in safe_path.split(os.sep):
            return None
        
        # Ensure the path is within the session workspace
        full_path = os.path.join(self.workspace_manager.session_workspace, safe_path)
        return full_path

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[List[dict]] = None,
    ) -> ToolImplOutput:
        file_path_str = tool_input.get("file_path")
        content = tool_input.get("content")

        if not file_path_str:
            return ToolImplOutput("", "Error: 'file_path' is required.")
        
        if content is None:
            return ToolImplOutput("", "Error: 'content' is required.")

        full_path = self._get_full_safe_path(file_path_str)
        if not full_path:
            return ToolImplOutput("", f"Error: Invalid or unsafe file path '{file_path_str}'.")

        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return ToolImplOutput(
                f"Successfully wrote content to '{file_path_str}'.",
                "File written successfully."
            )
        except Exception as e:
            return ToolImplOutput("", f"Error writing to file '{file_path_str}': {e}")
