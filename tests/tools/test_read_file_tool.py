import os
import pandas as pd
import pytest
from unittest.mock import MagicMock
from boss_agent.tools.read_file_tool import ReadFileTool
from boss_agent.utils import WorkspaceManager

@pytest.fixture
def workspace_manager(tmp_path):
    """Fixture to create a temporary workspace for testing."""
    session_path = tmp_path / "session"
    knowledge_base_path = tmp_path / "knowledge_base"
    session_path.mkdir()
    knowledge_base_path.mkdir()
    
    manager = MagicMock(spec=WorkspaceManager)
    manager.session_workspace = str(session_path)
    manager.root = str(knowledge_base_path)
    return manager

def test_read_xlsx_as_csv_fallback(workspace_manager):
    """
    Tests if the ReadFileTool can read a CSV file that has a .xlsx extension.
    """
    # 1. Create a dummy CSV content and save it with an .xlsx extension
    csv_content = "header1,header2\nvalue1,value2"
    fake_xlsx_path = os.path.join(workspace_manager.root, "fake_excel.xlsx")
    with open(fake_xlsx_path, "w") as f:
        f.write(csv_content)

    # 2. Instantiate the tool
    read_file_tool = ReadFileTool(workspace_manager=workspace_manager)

    # 3. Run the tool
    tool_input = {"path": "fake_excel.xlsx"}
    result = read_file_tool.run_impl(tool_input)

    # 4. Assert the outcome
    # The tool should successfully read the file and return its content as CSV
    expected_output_df = pd.DataFrame([["value1", "value2"]], columns=["header1", "header2"])
    expected_csv_output = expected_output_df.to_csv(index=False).strip()
    
    # The result.tool_output might have extra newlines, so we strip it
    actual_csv_output = result.tool_output.strip()

    assert actual_csv_output == expected_csv_output
    assert "Successfully read content" in result.tool_result_message

def test_read_regular_xlsx_file(workspace_manager):
    """
    Tests if the ReadFileTool can still read a regular, valid .xlsx file.
    """
    # 1. Create a valid .xlsx file
    df = pd.DataFrame([["a", "b"], ["c", "d"]], columns=["col1", "col2"])
    real_xlsx_path = os.path.join(workspace_manager.root, "real_excel.xlsx")
    df.to_excel(real_xlsx_path, index=False, sheet_name="TestSheet")

    # 2. Instantiate the tool
    read_file_tool = ReadFileTool(workspace_manager=workspace_manager)

    # 3. Run the tool
    tool_input = {"path": "real_excel.xlsx"}
    result = read_file_tool.run_impl(tool_input)

    # 4. Assert the outcome
    expected_csv_in_output = df.to_csv(index=False).strip()
    assert "Sheet: TestSheet" in result.tool_output
    assert expected_csv_in_output in result.tool_output
    assert "Successfully read content" in result.tool_result_message
