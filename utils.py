from argparse import ArgumentParser
import uuid
from pathlib import Path
from typing import Optional
from boss_agent.utils import WorkspaceManager
from boss_agent.utils.constants import DEFAULT_MODEL


def parse_common_args(parser: ArgumentParser):
    parser.add_argument(
        "--workspace",
        type=str,
        default="./workspace",
        help="Path to the workspace",
    )
    parser.add_argument(
        "--logs-path",
        type=str,
        default="agent_logs.txt",
        help="Path to save logs",
    )
    parser.add_argument(
        "--needs-permission",
        "-p",
        help="Ask for permission before executing commands",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--use-container-workspace",
        type=str,
        default=None,
        help="(Optional) Path to the container workspace to run commands in.",
    )
    parser.add_argument(
        "--docker-container-id",
        type=str,
        default=None,
        help="(Optional) Docker container ID to run commands in.",
    )
    parser.add_argument(
        "--minimize-stdout-logs",
        help="Minimize the amount of logs printed to stdout.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=None,
        help="Project ID to use for Anthropic",
    )
    parser.add_argument(
        "--region",
        type=str,
        default=None,
        help="Region to use for Anthropic",
    )
    parser.add_argument(
        "--memory-tool",
        type=str,
        default="compactify-memory",
        choices=["compactify-memory", "none", "simple"],
        help="Type of memory tool to use"
    )
    parser.add_argument(
        "--llm-client",
        type=str,
        default="anthropic-direct",
        choices=["anthropic-direct", "openai-direct"],
        help="LLM client to use (anthropic-direct or openai-direct for LMStudio/local)",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default=DEFAULT_MODEL,
        help="Name of the LLM model to use (e.g., claude-3-opus-20240229 or local-model-identifier for LMStudio)",
    )
    parser.add_argument(
        "--azure-model",
        action="store_true",
        default=False,
        help="Use Azure OpenAI model",
    )
    parser.add_argument(
        "--no-cot-model",
        action="store_false",
        dest="cot_model",
        default=True,
        help="Disable chain-of-thought model (enabled by default)",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Prompt to use for the LLM",
    )
    return parser


from datetime import datetime

def create_workspace_manager_for_connection(
    workspace_root: str, use_container_workspace: Optional[str] = None
):
    """Create a new workspace manager instance for a websocket connection."""
    # Create unique subdirectory for this connection in a 'sessions' folder
    # at the same level as the knowledge base.
    knowledge_base_path = Path(workspace_root).resolve()
    sessions_path = knowledge_base_path.parent / "sessions"
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    session_uuid = uuid.uuid4()
    connection_id = f"{timestamp}-{str(session_uuid)}"
    
    connection_workspace = sessions_path / connection_id
    connection_workspace.mkdir(parents=True, exist_ok=True)

    # Initialize workspace manager with the knowledge base as the root,
    # but with a specific session workspace for writes.
    container_workspace_path = Path(use_container_workspace) if use_container_workspace else None
    workspace_manager = WorkspaceManager(
        root=knowledge_base_path,
        session_workspace=connection_workspace,
        container_workspace=container_workspace_path,
    )

    return workspace_manager, session_uuid
