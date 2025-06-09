"""Tool for creating chart descriptions to be rendered by the frontend."""

import json
from typing import Any, Optional, List, Dict
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.tools.data_analysis_tool import DataAnalysisTool

class VisualizationTool(LLMTool):
    name = "create_chart"
    description = "Generates a chart placeholder string to be embedded in a report. The report generator will then replace this placeholder with a real chart."

    input_schema = {
        "type": "object",
        "properties": {
            "dataframe_id": {
                "type": "string",
                "description": "The ID of the dataframe to source the data from.",
            },
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie"],
                "description": "The type of chart to generate.",
            },
            "x_axis_column": {
                "type": "string",
                "description": "The column name to use for the X-axis.",
            },
            "y_axis_column": {
                "type": "string",
                "description": "The column name to use for the Y-axis.",
            },
            "title": {
                "type": "string",
                "description": "The title of the chart.",
            }
        },
        "required": ["dataframe_id", "chart_type", "x_axis_column", "y_axis_column", "title"],
    }

    def __init__(self, data_analysis_tool: DataAnalysisTool):
        super().__init__()
        self.data_analysis_tool = data_analysis_tool

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[List[dict]] = None,
    ) -> ToolImplOutput:
        df_id = tool_input.get("dataframe_id")
        chart_type = tool_input.get("chart_type")
        x_col = tool_input.get("x_axis_column")
        y_col = tool_input.get("y_axis_column")
        title = tool_input.get("title")

        if df_id not in self.data_analysis_tool.loaded_dataframes:
            return ToolImplOutput("", f"Error: Dataframe with ID '{df_id}' not found.")

        df = self.data_analysis_tool.loaded_dataframes[df_id]

        if x_col not in df.columns or y_col not in df.columns:
            return ToolImplOutput("", f"Error: One or both columns not found in dataframe '{df_id}'.")

        chart_data = {
            "chart_type": chart_type,
            "title": title,
            "x_axis": {"label": x_col, "data": df[x_col].tolist()},
            "y_axis": {"label": y_col, "data": df[y_col].tolist()},
        }

        # The tool output is a placeholder string that the report generator will recognize
        placeholder = f"[CHART:{json.dumps(tool_input)}]"
        
        return ToolImplOutput(
            placeholder,
            f"Chart placeholder created for '{title}'."
        )
