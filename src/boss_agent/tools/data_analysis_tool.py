"""Core tool for data analysis using pandas."""

import os
import pandas as pd
from typing import Any, Optional, List, Dict
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.utils import WorkspaceManager

class DataAnalysisTool(LLMTool):
    name = "data_analysis"
    description = "A tool for performing data analysis on structured files (CSV, Excel). It can load data, describe its structure, and perform calculations."

    input_schema = {
        "type": "object",
        "properties": {
            "sub_tool": {
                "type": "string",
                "enum": ["load_data", "describe_data", "calculate", "merge_data"],
                "description": "The specific sub-tool to use.",
            },
            "file_path": {
                "type": "string",
                "description": "The path to the data file for 'load_data'.",
            },
            "dataframe_id": {
                "type": "string",
                "description": "The ID of the dataframe for 'describe_data' or 'calculate'.",
            },
            "expression": {
                "type": "string",
                "description": "The calculation expression for 'calculate', e.g., 'sum(column_name)'.",
            },
            "left_dataframe_id": {
                "type": "string",
                "description": "The ID of the left dataframe for 'merge_data'.",
            },
            "right_dataframe_id": {
                "type": "string",
                "description": "The ID of the right dataframe for 'merge_data'.",
            },
            "on_key": {
                "type": "string",
                "description": "The column name to merge on. Required for 'merge_data'.",
            }
        },
        "required": ["sub_tool"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager
        self.loaded_dataframes: Dict[str, pd.DataFrame] = {}

    def _get_full_path(self, file_path: str) -> Optional[str]:
        """Get the full, safe path to a file, prioritizing the session workspace."""
        safe_path = os.path.normpath(os.path.join('/', file_path)).lstrip('/\\')
        if ".." in safe_path.split(os.sep):
            return None
        
        session_file = os.path.join(self.workspace_manager.session_workspace, safe_path)
        if os.path.exists(session_file):
            return session_file
        
        kb_file = os.path.join(self.workspace_manager.root, safe_path)
        if os.path.exists(kb_file):
            return kb_file
            
        return None

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[List[dict]] = None,
    ) -> ToolImplOutput:
        sub_tool = tool_input.get("sub_tool")

        if sub_tool == "load_data":
            return self._load_data(tool_input)
        elif sub_tool == "describe_data":
            return self._describe_data(tool_input)
        elif sub_tool == "calculate":
            return self._calculate(tool_input)
        elif sub_tool == "merge_data":
            return self._merge_data(tool_input)
        else:
            return ToolImplOutput("", f"Error: Unknown sub_tool '{sub_tool}'.")

    def _load_data(self, tool_input: dict[str, Any]) -> ToolImplOutput:
        file_path_str = tool_input.get("file_path")
        if not file_path_str:
            return ToolImplOutput("", "Error: 'file_path' is required for 'load_data'.")

        full_path = self._get_full_path(file_path_str)
        if not full_path:
            return ToolImplOutput("", f"Error: File not found at '{file_path_str}'.")

        try:
            if full_path.endswith(".csv"):
                df = pd.read_csv(full_path)
            elif full_path.endswith(".xlsx"):
                df = pd.read_excel(full_path)
            elif full_path.endswith(".json"):
                df = pd.read_json(full_path)
            else:
                return ToolImplOutput("", f"Error: Unsupported file type '{os.path.basename(full_path)}'.")

            df_id = f"df_{len(self.loaded_dataframes) + 1}"
            self.loaded_dataframes[df_id] = df

            return ToolImplOutput(
                f"Successfully loaded '{file_path_str}' as dataframe with ID: {df_id}. Use 'describe_data' to see its structure.",
                "Data loaded successfully."
            )
        except Exception as e:
            return ToolImplOutput("", f"Error loading data from '{file_path_str}': {e}")

    def _describe_data(self, tool_input: dict[str, Any]) -> ToolImplOutput:
        df_id = tool_input.get("dataframe_id")
        if not df_id:
            return ToolImplOutput("", "Error: 'dataframe_id' is required for 'describe_data'.")
        
        if df_id not in self.loaded_dataframes:
            return ToolImplOutput("", f"Error: Dataframe with ID '{df_id}' not found.")

        df = self.loaded_dataframes[df_id]
        
        description = {
            "columns": list(df.columns),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head().to_dict('records')
        }
        
        return ToolImplOutput(str(description), "Data described successfully.")

    def _calculate(self, tool_input: dict[str, Any]) -> ToolImplOutput:
        df_id = tool_input.get("dataframe_id")
        expression = tool_input.get("expression")

        if not df_id or not expression:
            return ToolImplOutput("", "Error: 'dataframe_id' and 'expression' are required for 'calculate'.")

        if df_id not in self.loaded_dataframes:
            return ToolImplOutput("", f"Error: Dataframe with ID '{df_id}' not found.")

        df = self.loaded_dataframes[df_id]

        # Simple expression parser: "agg(column)"
        try:
            agg_func, rest = expression.split('(', 1)
            column_name = rest.rsplit(')', 1)[0]

            if column_name not in df.columns:
                return ToolImplOutput("", f"Error: Column '{column_name}' not found in dataframe '{df_id}'.")

            if agg_func == 'sum':
                result = df[column_name].sum()
            elif agg_func == 'mean':
                result = df[column_name].mean()
            elif agg_func == 'count':
                result = df[column_name].count()
            else:
                return ToolImplOutput("", f"Error: Unsupported aggregation function '{agg_func}'.")

            return ToolImplOutput(str(result), f"Successfully calculated {expression} on {df_id}.")
        except Exception as e:
            return ToolImplOutput("", f"Error evaluating expression '{expression}': {e}")

    def _merge_data(self, tool_input: dict[str, Any]) -> ToolImplOutput:
        left_df_id = tool_input.get("left_dataframe_id")
        right_df_id = tool_input.get("right_dataframe_id")
        on_key = tool_input.get("on_key")

        if not left_df_id or not right_df_id or not on_key:
            return ToolImplOutput("", "Error: 'left_dataframe_id', 'right_dataframe_id', and 'on_key' are required for 'merge_data'.")

        if left_df_id not in self.loaded_dataframes or right_df_id not in self.loaded_dataframes:
            return ToolImplOutput("", f"Error: One or both dataframe IDs not found.")

        left_df = self.loaded_dataframes[left_df_id]
        right_df = self.loaded_dataframes[right_df_id]

        if on_key not in left_df.columns or on_key not in right_df.columns:
            return ToolImplOutput("", f"Error: Merge key '{on_key}' not found in one or both dataframes.")

        try:
            merged_df = pd.merge(left_df, right_df, on=on_key)
            
            df_id = f"df_{len(self.loaded_dataframes) + 1}"
            self.loaded_dataframes[df_id] = merged_df

            return ToolImplOutput(
                f"Successfully merged dataframes '{left_df_id}' and '{right_df_id}' into new dataframe with ID: {df_id}. Use 'describe_data' to see its structure.",
                "Data merged successfully."
            )
        except Exception as e:
            return ToolImplOutput("", f"Error merging dataframes: {e}")
