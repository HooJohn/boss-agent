"""Tool for generating reports based on internal knowledge base."""
import os
from typing import Any, Optional
from boss_agent.tools.base import LLMTool, ToolImplOutput
from boss_agent.utils.workspace_manager import WorkspaceManager
from boss_agent.llm.base import LLMClient, TextPrompt, TextResult
from boss_agent.llm.message_history import MessageHistory
from boss_agent.tools.data_analysis_tool import DataAnalysisTool
from boss_agent.tools.visualization_tool import VisualizationTool

class ReportGeneratorTool(LLMTool):
    name = "report_generator"
    description = "Generates a professional, structured report based on a user's query and provided data."

    input_schema = {
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "description": "The type of report to generate (e.g., 'balance_sheet', 'income_statement').",
            },
            "time_dimension": {
                "type": "string",
                "description": "The time dimension for the report (e.g., '2024-Q2', '2023').",
            },
            "department": {
                "type": "string",
                "description": "The department for which the report is generated (e.g., 'finance', 'hr').",
            },
        },
        "required": ["report_type", "time_dimension", "department"],
    }

    def __init__(self, workspace_manager: WorkspaceManager, client: LLMClient, data_analysis_tool: DataAnalysisTool, visualization_tool: VisualizationTool):
        super().__init__()
        self.workspace_manager = workspace_manager
        self.client = client
        self.data_analysis_tool = data_analysis_tool
        self.visualization_tool = visualization_tool

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        report_type = tool_input.get("report_type")
        time_dimension = tool_input.get("time_dimension")
        department = tool_input.get("department")

        # Construct the file path based on the input
        # This is a simplified example. You might need a more robust way to map these inputs to file paths.
        file_name_map = {
            "balance_sheet": "通用账本交易明细",
            "income_statement": "通用账本交易明细",
            "cash_flow_statement": "通用账本交易明细",
        }
        file_name_prefix = file_name_map.get(str(report_type), "通用账本交易明细")
        
        # Simplified time mapping. You might need more complex logic.
        year = str(time_dimension).split('-')[0]
        file_path = os.path.join(str(self.workspace_manager.root), 'knowledge_base', str(department))

        # Find the relevant file
        target_file = None
        for root, _, files in os.walk(file_path):
            for file in files:
                if file_name_prefix in file and year in file:
                    target_file = os.path.join(root, file)
                    break
            if target_file:
                break

        if not target_file:
            return ToolImplOutput("", f"Error: Data file not found for the given criteria.")

        # Load the data using the data analysis tool
        load_input = {"sub_tool": "load_data", "file_path": target_file}
        load_result = self.data_analysis_tool.run_impl(load_input)
        
        tool_output = load_result.tool_output
        if not tool_output or "Successfully loaded" not in str(tool_output):
            return ToolImplOutput("", f"Error: Failed to load data from {target_file}.")

        # Extract dataframe_id from the output string
        try:
            df_id = str(tool_output).split("ID: ")[1].split('.')[0]
        except IndexError:
            return ToolImplOutput("", f"Error: Could not extract dataframe_id from tool output: {tool_output}")
        
        df = self.data_analysis_tool.loaded_dataframes[df_id]
        data_table = df.head().to_markdown(index=False) # Show a preview

        # Generate a chart
        chart_input = {
            "dataframe_id": df_id,
            "chart_type": "bar",
            "x_axis_column": df.columns[0],
            "y_axis_column": df.columns[1],
            "title": f"{report_type} for {time_dimension}",
        }
        chart_result = self.visualization_tool.run_impl(chart_input)
        charts_section = ""
        if chart_result.tool_output:
            charts_section = str(chart_result.tool_output)


        # For this example, we'll just generate a simple summary.
        # In a real scenario, you would perform more complex analysis here.
        summary_points = [
            f"This report is a {report_type} for the period {time_dimension}.",
            "The data has been successfully loaded and is ready for analysis.",
            "Below is a preview of the data.",
        ]
        summary_text = "\n".join(f"- {point}" for point in summary_points)

        prompt = f"""
        Based on the user's query and the following data, generate a professional, well-structured report in Markdown format.

        User's Query: Generate a {report_type} for {time_dimension}

        Key Findings:
        {summary_text}

        Visualizations:
        {charts_section}

        Detailed Data Preview:
        {data_table}

        The report must include:
        1. A clear title.
        2. An executive summary of the key findings.
        3. Any generated charts.
        4. The detailed data preview presented in a Markdown table.
        """

        try:
            response_blocks, _ = self.client.generate(
                messages=[[TextPrompt(text=prompt)]],
                max_tokens=4096,
            )
            report = ""
            for block in response_blocks:
                if isinstance(block, TextResult):
                    report = block.text
                    break
            return ToolImplOutput(report, "Report generated successfully.")
        except Exception as e:
            return ToolImplOutput("", f"Failed to generate report from LLM: {e}")
