"""Tool for recursively listing files in a directory."""

import os
from typing import Any, Optional, List
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.llm.message_history import MessageHistory
from boss_agent.utils import WorkspaceManager

class ListFilesTool(LLMTool):
    name = "list_files"
    description = "Recursively lists all files and directories within a specified path in the knowledge base."

    input_schema = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The subdirectory path to start listing from, relative to the knowledge base root. Defaults to the root.",
                "default": ".",
            }
        },
        "required": [],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        path_filter = tool_input.get("path", ".")

        # If the agent mistakenly uses 'knowledge_base' as the path,
        # correct it to '.' to represent the root of the workspace,
        # as the workspace root is already configured to be the knowledge base path.
        if path_filter == 'knowledge_base':
            path_filter = '.'

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

        output_lines: List[str] = []
        
        # --- Walk through knowledge base path ---
        if os.path.isdir(kb_path):
            for root, dirs, files in os.walk(kb_path):
                relative_root = os.path.relpath(root, kb_path)
                if relative_root == ".":
                    relative_root = ""
                
                # Add directories to output
                for d in sorted(dirs):
                    output_lines.append(os.path.join(relative_root, d) + "/")
                
                # Add files to output
                for f in sorted(files):
                    output_lines.append(os.path.join(relative_root, f))

        # --- Walk through session workspace path (if different) ---
        if kb_path != session_path and os.path.isdir(session_path):
             for root, dirs, files in os.walk(session_path):
                relative_root = os.path.relpath(root, session_path)
                if relative_root == ".":
                    relative_root = ""
                
                # Add directories to output
                for d in sorted(dirs):
                    line = "session/" + os.path.join(relative_root, d) + "/"
                    if line not in output_lines:
                        output_lines.append(line)
                
                # Add files to output
                for f in sorted(files):
                    line = "session/" + os.path.join(relative_root, f)
                    if line not in output_lines:
                        output_lines.append(line)

        if not output_lines:
            return ToolImplOutput(f"The directory '{path_filter}' is empty.", "Successfully listed an empty directory.")

        result = f"Contents of '{path_filter}':\n" + "\n".join(output_lines)
        return ToolImplOutput(result, f"Successfully listed contents of '{path_filter}'.")
