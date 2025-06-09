"""Tool for performing data aggregations on files."""

import os
import pandas as pd
from typing import Any, Optional
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.llm.message_history import MessageHistory
from boss_agent.utils import WorkspaceManager

class DataAggregationTool(LLMTool):
    name = "data_aggregation"
    description = "Performs an aggregation on a specified file. Currently supports 'count_rows' for CSV files."

    input_schema = {
        "type": "object",
        "properties": {
            "aggregation_mode": {
                "type": "string",
                "enum": ["count_rows"],
                "description": "The aggregation to perform. Currently only 'count_rows' is supported.",
            },
            "aggregation_path": {
                "type": "string",
                "description": "The full path to the file to be aggregated, relative to the knowledge base root.",
            }
        },
        "required": ["aggregation_mode", "aggregation_path"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        aggregation_mode = tool_input.get("aggregation_mode")
        aggregation_path = tool_input.get("aggregation_path")

        if not aggregation_mode or not aggregation_path:
            return ToolImplOutput("", "Error: 'aggregation_mode' and 'aggregation_path' are required.")

        if aggregation_mode == "count_rows":
            # Prioritize session path
            file_to_agg = os.path.join(self.workspace_manager.session_workspace, aggregation_path)
            if not os.path.exists(file_to_agg):
                file_to_agg = os.path.join(self.workspace_manager.root, aggregation_path)

            if not os.path.exists(file_to_agg):
                return ToolImplOutput("", f"Error: File not found at '{aggregation_path}'.")

            try:
                # Assuming the file is a CSV for row counting
                df = pd.read_csv(file_to_agg)
                row_count = len(df)
                return ToolImplOutput(str(row_count), f"Successfully counted {row_count} rows in '{aggregation_path}'.")
            except Exception as e:
                return ToolImplOutput("", f"Error counting rows in '{aggregation_path}': {e}")
        else:
            return ToolImplOutput("", f"Error: Unsupported aggregation mode '{aggregation_mode}'.")
