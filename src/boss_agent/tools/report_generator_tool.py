"""Tool for generating reports based on internal knowledge base."""

import os
from typing import Any, Optional, List
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.utils import WorkspaceManager
from boss_agent.llm.base import LLMClient

class ReportGeneratorTool(LLMTool):
    name = "generate_report"
    description = "Generates a report based on a specified type and time dimension by searching the internal knowledge base."

    input_schema = {
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "description": "The type of report to generate (e.g., 'income_statement', 'sales_summary').",
            },
            "time_dimension": {
                "type": "string",
                "description": "The time dimension for the report (e.g., '2024-Q2', '2023').",
            },
            "department": {
                "type": "string",
                "description": "The department to generate the report for (e.g., 'finance', 'sales').",
            }
        },
        "required": ["report_type", "time_dimension", "department"],
    }

    def __init__(self, workspace_manager: WorkspaceManager, client: LLMClient):
        super().__init__()
        self.workspace_manager = workspace_manager
        self.client = client

    def _find_relevant_files(self, department: str, time_dimension: str, report_type: str) -> List[str]:
        """Find files in the knowledge base that match the criteria."""
        search_path = os.path.join(self.workspace_manager.root, department)
        if not os.path.isdir(search_path):
            return []

        found_files = []
        for root, _, files in os.walk(search_path):
            for file in files:
                # A simple matching logic based on file naming convention
                if time_dimension in file and report_type.replace('_', '-') in file:
                    found_files.append(os.path.join(root, file))
        return found_files

    def _read_file_content(self, file_path: str) -> str:
        """Reads the content of a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {file_path}: {e}"

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[List[dict]] = None,
    ) -> ToolImplOutput:
        report_type = tool_input.get("report_type")
        time_dimension = tool_input.get("time_dimension")
        department = tool_input.get("department")

        relevant_files = self._find_relevant_files(department, time_dimension, report_type)

        if not relevant_files:
            return ToolImplOutput(f"No data found for {department} {report_type} in {time_dimension}.", "Report generation failed.")

        # For simplicity, we'll use the content of the first found file.
        # A more advanced implementation would aggregate data from all found files.
        file_content = self._read_file_content(relevant_files[0])

        # A simple prompt template. This would be more sophisticated in a real application.
        prompt = f"""
        Based on the following data, generate a {report_type.replace('_', ' ')} for {time_dimension}.
        The report should be well-structured, with a title, a summary, and a data table.

        Data:
        ---
        {file_content}
        ---
        """

        # Call the LLM to generate the report
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model="claude-3-7-sonnet@20250219", # Or any other suitable model
            )
            report = response.completion
            return ToolImplOutput(report, "Report generated successfully.")
        except Exception as e:
            return ToolImplOutput("", f"Failed to generate report from LLM: {e}")
