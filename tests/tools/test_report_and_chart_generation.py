import unittest
import pandas as pd
from unittest.mock import MagicMock

# Adjust the import path based on your project structure
from boss_agent.tools.data_analysis_tool import DataAnalysisTool
from boss_agent.tools.visualization_tool import VisualizationTool
from boss_agent.tools.report_generator_tool import ReportGeneratorTool

class TestReportAndChartGeneration(unittest.TestCase):

    def setUp(self):
        """Set up the tools for testing."""
        # Mock the LLM client and WorkspaceManager as they are not the focus of this test
        mock_llm_client = MagicMock()
        mock_workspace_manager = MagicMock()

        # Initialize the tools
        self.data_analysis_tool = DataAnalysisTool(workspace_manager=mock_workspace_manager)
        self.visualization_tool = VisualizationTool(data_analysis_tool=self.data_analysis_tool)
        self.report_generator = ReportGeneratorTool(
            client=mock_llm_client,
            data_analysis_tool=self.data_analysis_tool,
            visualization_tool=self.visualization_tool
        )

    def test_full_report_generation_with_chart(self):
        """
        Tests the full pipeline from a dataframe to a final report with a chart,
        ensuring the chart's JSON is correctly embedded.
        """
        # 1. Simulate loading data into the data_analysis_tool
        df_id = "test_df"
        test_data = {
            'Product': ['A', 'B', 'C'],
            'Sales': [100, 150, 80]
        }
        test_df = pd.DataFrame(test_data)
        self.data_analysis_tool.loaded_dataframes[df_id] = test_df

        # 2. Define the inputs for the report_generator tool
        report_title = "Test Sales Report"
        report_summary = "This is a summary of sales."
        data_table_md = test_df.to_markdown(index=False)
        charts_to_create = [
            {
                "dataframe_id": df_id,
                "chart_type": "bar",
                "x_axis_column": "Product",
                "y_axis_column": "Sales",
                "title": "Sales by Product"
            }
        ]

        # 3. Call the report_generator tool
        report_input = {
            "title": report_title,
            "summary": report_summary,
            "data_table_markdown": data_table_md,
            "charts": charts_to_create
        }
        result = self.report_generator.run_impl(report_input)
        final_report = result.tool_output

        # 4. Assertions: Verify the report content
        self.assertIn(f"# {report_title}", final_report)
        self.assertIn(f"## Executive Summary\n{report_summary}", final_report)
        self.assertIn(f"## Detailed Data\n{data_table_md}", final_report)

        # 4a. CRITICAL: Assert that a correctly formatted JSON block for the chart exists
        self.assertIn("## Visualizations", final_report)
        self.assertIn("```json", final_report)
        self.assertIn('"visualization":', final_report)
        self.assertIn('"chart_type": "bar"', final_report)
        self.assertIn('"title": "Sales by Product"', final_report)
        self.assertIn('"x_axis": {"label": "Product", "data": ["A", "B", "C"]}', final_report)
        self.assertIn('"y_axis": {"label": "Sales", "data": [100, 150, 80]}', final_report)
        self.assertIn("```", final_report)

        print("\n--- Test Report Generation Passed ---")
        print(final_report)
        print("------------------------------------")

if __name__ == '__main__':
    unittest.main()
