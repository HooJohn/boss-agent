"""Tool for generating reports based on internal knowledge base."""
import os
from typing import Any, Optional
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.llm.base import LLMClient
from boss_agent.llm.message_history import MessageHistory
from boss_agent.tools.data_analysis_tool import DataAnalysisTool
from boss_agent.tools.visualization_tool import VisualizationTool

class ReportGeneratorTool(LLMTool):
    name = "report_generator"
    description = "Generates a professional, structured report by assembling provided text, data tables, and charts. This tool does not call an LLM; it deterministically assembles the report."

    input_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The main title of the report.",
            },
            "summary": {
                "type": "string",
                "description": "A brief summary or key findings to include in the report.",
            },
            "data_table_markdown": {
                "type": "string",
                "description": "A string containing a fully formatted Markdown table of the detailed data.",
            },
            "charts": {
                "type": "array",
                "description": "A list of chart descriptions to be generated and included in the report.",
                "items": {
                    "type": "object",
                    "properties": {
                        "dataframe_id": {"type": "string"},
                        "chart_type": {"type": "string", "enum": ["bar", "line", "pie"]},
                        "x_axis_column": {"type": "string"},
                        "y_axis_column": {"type": "string"},
                        "title": {"type": "string"},
                    },
                    "required": ["dataframe_id", "chart_type", "x_axis_column", "y_axis_column", "title"],
                }
            }
        },
        "required": ["title", "summary", "data_table_markdown"],
    }

    def __init__(self, client: LLMClient, data_analysis_tool: DataAnalysisTool, visualization_tool: VisualizationTool, **kwargs):
        super().__init__()
        self.client = client # Retained for potential future use, but not for main report generation
        self.data_analysis_tool = data_analysis_tool
        self.visualization_tool = visualization_tool

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        title = tool_input.get("title", "Untitled Report")
        summary = tool_input.get("summary", "")
        data_table = tool_input.get("data_table_markdown", "")
        charts_to_generate = tool_input.get("charts", [])

        charts_section = ""
        for chart_input in charts_to_generate:
            chart_result = self.visualization_tool.run_impl(chart_input)
            if chart_result.tool_output:
                # Format the chart JSON into a markdown code block for the frontend to render
                charts_section += f"### {chart_input.get('title', 'Chart')}\n"
                charts_section += f"```json\n{chart_result.tool_output}\n```\n\n"

        # Deterministically assemble the report using an f-string template
        report = f"""
# {title}

## Executive Summary
{summary}

## Visualizations
{charts_section if charts_section else "No visualizations were generated for this report."}

## Detailed Data
{data_table}
"""
        
        return ToolImplOutput(report.strip(), "Report assembled successfully.")
