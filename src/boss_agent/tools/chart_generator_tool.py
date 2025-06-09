"""Tool for generating chart images from dataframes."""

import os
import uuid
import matplotlib.pyplot as plt
from typing import Any, Optional, List
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.tools.data_analysis_tool import DataAnalysisTool
from boss_agent.utils import WorkspaceManager

class GenerateChartImageTool(LLMTool):
    name = "generate_chart_image"
    description = "Generates a chart image from a dataframe and saves it to a file. Returns the path to the generated image."

    input_schema = {
        "type": "object",
        "properties": {
            "dataframe_id": {
                "type": "string",
                "description": "The ID of the dataframe to source the data from.",
            },
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie", "scatter"],
                "description": "The type of chart to generate.",
            },
            "x_axis_column": {
                "type": "string",
                "description": "The column name to use for the X-axis.",
            },
            "y_axis_column": {
                "type": "string",
                "description": "The column name(s) to use for the Y-axis. Can be a single column or a list for multi-line charts.",
            },
            "title": {
                "type": "string",
                "description": "The title of the chart.",
            },
            "output_filename": {
                "type": "string",
                "description": "Optional: The desired filename for the output image. If not provided, a unique name will be generated.",
            }
        },
        "required": ["dataframe_id", "chart_type", "x_axis_column", "y_axis_column", "title"],
    }

    def __init__(self, data_analysis_tool: DataAnalysisTool, workspace_manager: WorkspaceManager):
        super().__init__()
        self.data_analysis_tool = data_analysis_tool
        self.workspace_manager = workspace_manager

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[List[dict]] = None,
    ) -> ToolImplOutput:
        df_id = tool_input.get("dataframe_id")
        chart_type = tool_input.get("chart_type")
        x_col = tool_input.get("x_axis_column")
        y_cols = tool_input.get("y_axis_column")
        title = tool_input.get("title")
        output_filename = tool_input.get("output_filename")

        if df_id not in self.data_analysis_tool.loaded_dataframes:
            return ToolImplOutput("", f"Error: Dataframe with ID '{df_id}' not found.")

        df = self.data_analysis_tool.loaded_dataframes[df_id]

        if not isinstance(y_cols, list):
            y_cols = [y_cols]

        if x_col not in df.columns or not all(y_col in df.columns for y_col in y_cols):
            return ToolImplOutput("", f"Error: One or more columns not found in dataframe '{df_id}'.")

        plt.figure(figsize=(10, 6))

        if chart_type == 'bar':
            for y_col in y_cols:
                plt.bar(df[x_col], df[y_col], label=y_col)
        elif chart_type == 'line':
            for y_col in y_cols:
                plt.plot(df[x_col], df[y_col], marker='o', label=y_col)
        elif chart_type == 'pie':
            if len(y_cols) > 1:
                return ToolImplOutput("", "Error: Pie charts only support a single y-axis column.")
            plt.pie(df[y_cols[0]], labels=df[x_col], autopct='%1.1f%%', startangle=140)
            plt.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
        elif chart_type == 'scatter':
            if len(y_cols) > 1:
                return ToolImplOutput("", "Error: Scatter charts only support a single y-axis column.")
            plt.scatter(df[x_col], df[y_cols[0]])
        
        plt.title(title)
        plt.xlabel(x_col)
        plt.ylabel(y_cols[0] if len(y_cols) == 1 else 'Values')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        # Ensure the charts directory exists
        charts_dir = self.workspace_manager.workspace_path("charts")
        os.makedirs(charts_dir, exist_ok=True)

        if not output_filename:
            output_filename = f"chart_{uuid.uuid4()}.png"
        
        output_path = os.path.join(charts_dir, output_filename)
        
        plt.savefig(output_path)
        plt.close()

        relative_path = os.path.relpath(output_path, self.workspace_manager.root)

        return ToolImplOutput(
            str(relative_path),
            f"Chart successfully generated and saved to '{relative_path}'."
        )
