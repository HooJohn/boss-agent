"""Tool for extracting structured information from unstructured documents."""

import os
import json
from typing import Any, Optional

from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.llm.base import LLMClient, TextPrompt, TextResult
from boss_agent.llm.message_history import MessageHistory
from boss_agent.utils import WorkspaceManager
from boss_agent.utils.file_reader import read_file_content

class ExtractInfoTool(LLMTool):
    name = "extract_info"
    description = "Extracts structured information from a document (like Word, PDF, TXT) based on a provided schema or list of fields."

    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file from which to extract information.",
            },
            "info_to_extract": {
                "type": "string",
                "description": "A JSON schema or a comma-separated list of fields describing the information to extract.",
            },
        },
        "required": ["file_path", "info_to_extract"],
    }

    def __init__(self, llm: LLMClient, workspace_manager: WorkspaceManager):
        super().__init__()
        self.llm = llm
        self.workspace_manager = workspace_manager

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        file_path = tool_input.get("file_path")
        info_to_extract = tool_input.get("info_to_extract")

        if not file_path or not info_to_extract:
            return ToolImplOutput("", "Error: 'file_path' and 'info_to_extract' are required.")

        # Construct full path
        full_path = os.path.join(self.workspace_manager.root, file_path)
        if not os.path.exists(full_path):
             # Check session workspace as a fallback
            full_path = os.path.join(self.workspace_manager.session_workspace, file_path)
            if not os.path.exists(full_path):
                return ToolImplOutput("", f"Error: File not found at '{file_path}'.")

        # 1. Read file content using the shared utility
        content = read_file_content(full_path, self.workspace_manager)
        if not content or content.startswith("Error"):
            return ToolImplOutput("", f"Error reading or processing file: {content}")

        # 2. Construct the prompt for the LLM
        prompt = f"""
        From the following document content, please extract the information requested.
        Return the result as a valid JSON object.

        **Extraction Requirements:**
        {info_to_extract}

        **Document Content:**
        ---
        {content[:15000]} 
        ---

        **JSON Output:**
        """

        # 3. Send to LLM and get the structured result
        response_text = ""
        try:
            response, _ = self.llm.generate(
                messages=[[TextPrompt(text=prompt)]],
                max_tokens=4096,
            )
            
            if response and isinstance(response[0], TextResult):
                response_text = response[0].text

            result_json = json.loads(response_text)
            result_str = json.dumps(result_json, indent=2, ensure_ascii=False)
            return ToolImplOutput(result_str, f"Successfully extracted information from '{file_path}'.")
        except json.JSONDecodeError:
            return ToolImplOutput("", f"Error: The model did not return a valid JSON object. Raw output: {response_text}")
        except Exception as e:
            return ToolImplOutput("", f"An unexpected error occurred during LLM processing: {e}")
