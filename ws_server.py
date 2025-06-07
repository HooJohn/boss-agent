#!/usr/bin/env python3
"""
FastAPI WebSocket Server for the Agent.

This script provides a WebSocket interface for interacting with the Agent,
allowing real-time communication with a frontend application.
"""

import os
import argparse
import asyncio
import json
import logging
import uuid
import configparser
from pathlib import Path
from typing import Dict, List, Set, Any
from dotenv import load_dotenv

load_dotenv()

import uvicorn
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Request,
    HTTPException,
)

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anyio
import base64
from sqlalchemy import asc, text

from boss_agent.core.event import RealtimeEvent, EventType
from boss_agent.db.models import Event
from boss_agent.utils.constants import DEFAULT_MODEL, TOKEN_BUDGET, UPLOAD_FOLDER_NAME
from utils import parse_common_args, create_workspace_manager_for_connection
from boss_agent.agents.anthropic_fc import AnthropicFC
from boss_agent.agents.base import BaseAgent
from boss_agent.llm.base import LLMClient
from boss_agent.utils import WorkspaceManager
from boss_agent.llm import get_client
from boss_agent.utils.prompt_generator import enhance_user_prompt

from fastapi.staticfiles import StaticFiles

from boss_agent.llm.context_manager.llm_summarizing import LLMSummarizingContextManager
from boss_agent.llm.token_counter import TokenCounter
from boss_agent.db.manager import DatabaseManager
from boss_agent.tools import get_system_tools
from boss_agent.prompts.system_prompt import SYSTEM_PROMPT, SYSTEM_PROMPT_WITH_SEQ_THINKING

MAX_OUTPUT_TOKENS_PER_TURN = 32000
MAX_TURNS = 200


app = FastAPI(title="Agent WebSocket API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logger = logging.getLogger("websocket_server")
logger.setLevel(logging.INFO)

active_connections: Set[WebSocket] = set()
active_agents: Dict[WebSocket, BaseAgent] = {}
active_tasks: Dict[WebSocket, asyncio.Task] = {}
message_processors: Dict[WebSocket, asyncio.Task] = {}
global_args = None


def map_model_name_to_client(model_name: str, ws_content: Dict[str, Any]) -> LLMClient:
    if "claude" in model_name:
        return get_client(
            "anthropic-direct",
            model_name=model_name,
            use_caching=False,
            project_id=global_args.project_id,
            region=global_args.region,
            thinking_tokens=ws_content['tool_args']['thinking_tokens'],
        )
    elif "gemini" in model_name:
        return get_client(
            "gemini-direct",
            model_name=model_name,
            project_id=global_args.project_id,
            region=global_args.region,
        )
    elif model_name in ["o3", "o4-mini", "gpt-4.1", "gpt-4o"]:
        return get_client(
            "openai-direct",
            model_name=model_name,
            azure_model=ws_content.get("azure_model", True),
            cot_model=ws_content.get("cot_model", False),
        )
    else:
        raise ValueError(f"Unknown model name: {model_name}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)

    config = configparser.ConfigParser()
    config.read('config.ini')
    knowledge_base_path = config.get('knowledge_base', 'path', fallback=global_args.workspace)

    workspace_manager, session_uuid = create_workspace_manager_for_connection(
        knowledge_base_path, global_args.use_container_workspace
    )
    print(f"Workspace manager created for knowledge base: {workspace_manager}")

    try:
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.CONNECTION_ESTABLISHED,
                content={
                    "message": "Connected to Agent WebSocket Server",
                    "workspace_path": str(workspace_manager.root),
                },
            ).model_dump()
        )

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                content = message.get("content", {})

                if msg_type == "init_agent":
                    model_name = content.get("model_name", DEFAULT_MODEL)
                    client = map_model_name_to_client(model_name, content)
                    tool_args = content.get("tool_args", {})
                    agent = create_agent_for_connection(
                        client, session_uuid, workspace_manager, websocket, tool_args
                    )
                    active_agents[websocket] = agent
                    message_processor = agent.start_message_processing()
                    message_processors[websocket] = message_processor
                    await websocket.send_json(
                        RealtimeEvent(
                            type=EventType.AGENT_INITIALIZED,
                            content={"message": "Agent initialized"},
                        ).model_dump()
                    )

                elif msg_type == "query":
                    if websocket in active_tasks and not active_tasks[websocket].done():
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.ERROR,
                                content={"message": "A query is already being processed"},
                            ).model_dump()
                        )
                        continue

                    user_input = content.get("text", "")
                    resume = content.get("resume", False)
                    files = content.get("files", [])
                    search_mode = content.get("search_mode", "all")
                    tool_choice = content.get("tool_choice")

                    await websocket.send_json(
                        RealtimeEvent(
                            type=EventType.PROCESSING,
                            content={"message": "Processing your request..."},
                        ).model_dump()
                    )

                    task = asyncio.create_task(
                        run_agent_async(websocket, user_input, resume, files, search_mode, tool_choice)
                    )
                    active_tasks[websocket] = task

                elif msg_type == "cancel":
                    agent = active_agents.get(websocket)
                    if agent:
                        agent.cancel()
                        await websocket.send_json(
                            RealtimeEvent(
                                type=EventType.SYSTEM,
                                content={"message": "Query cancelled"},
                            ).model_dump()
                        )

            except json.JSONDecodeError:
                await websocket.send_json(
                    RealtimeEvent(
                        type=EventType.ERROR, content={"message": "Invalid JSON format"}
                    ).model_dump()
                )
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await websocket.send_json(
                    RealtimeEvent(
                        type=EventType.ERROR,
                        content={"message": f"Error processing request: {str(e)}"},
                    ).model_dump()
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        cleanup_connection(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        cleanup_connection(websocket)


async def run_agent_async(
    websocket: WebSocket, user_input: str, resume: bool = False, files: List[str] = [], search_mode: str = "all", tool_choice: Dict[str, Any] = None
):
    agent = active_agents.get(websocket)
    if not agent:
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.ERROR,
                content={"message": "Agent not initialized for this connection"},
            ).model_dump()
        )
        return

    try:
        agent.message_queue.put_nowait(
            RealtimeEvent(type=EventType.USER_MESSAGE, content={"text": user_input})
        )
        await anyio.to_thread.run_sync(
            agent.run_agent, user_input, files, resume, tool_choice, abandon_on_cancel=True
        )
    except Exception as e:
        logger.error(f"Error running agent: {str(e)}")
        import traceback
        traceback.print_exc()
        await websocket.send_json(
            RealtimeEvent(
                type=EventType.ERROR,
                content={"message": f"Error running agent: {str(e)}"},
            ).model_dump()
        )
    finally:
        if websocket in active_tasks:
            del active_tasks[websocket]


def cleanup_connection(websocket: WebSocket):
    if websocket in active_connections:
        active_connections.remove(websocket)
    if websocket in active_agents:
        agent = active_agents[websocket]
        agent.websocket = None
        if websocket in message_processors:
            del message_processors[websocket]
    if websocket in active_tasks and not active_tasks[websocket].done():
        active_tasks[websocket].cancel()
        del active_tasks[websocket]
    if websocket in active_agents:
        del active_agents[websocket]


def create_agent_for_connection(
    client: LLMClient,
    session_id: uuid.UUID,
    workspace_manager: WorkspaceManager,
    websocket: WebSocket,
    tool_args: Dict[str, Any],
    search_mode: str = "all",
):
    global global_args
    device_id = websocket.query_params.get("device_id")
    logger_for_agent_logs = logging.getLogger(f"agent_logs_{id(websocket)}")
    logger_for_agent_logs.setLevel(logging.DEBUG)
    logger_for_agent_logs.propagate = False

    if not logger_for_agent_logs.handlers:
        logger_for_agent_logs.addHandler(logging.FileHandler(global_args.logs_path))
        if not global_args.minimize_stdout_logs:
            logger_for_agent_logs.addHandler(logging.StreamHandler())

    db_manager = DatabaseManager()
    db_manager.create_session(
        device_id=device_id,
        session_uuid=session_id,
        workspace_path=workspace_manager.root,
    )
    logger_for_agent_logs.info(
        f"Created new session {session_id} with workspace at {workspace_manager.root}"
    )

    token_counter = TokenCounter()
    context_manager = LLMSummarizingContextManager(
        client=client,
        token_counter=token_counter,
        logger=logger_for_agent_logs,
        token_budget=TOKEN_BUDGET,
    )

    queue = asyncio.Queue()
    tools = get_system_tools(
        client=client,
        workspace_manager=workspace_manager,
        message_queue=queue,
        container_id=global_args.docker_container_id,
        ask_user_permission=global_args.needs_permission,
        tool_args=tool_args,
    )
    if search_mode == "internal":
        tools = [tool for tool in tools if tool.name != "web_search"]
    elif search_mode == "external":
        tools = [tool for tool in tools if tool.name != "internal_search"]
    
    agent = AnthropicFC(
        system_prompt=SYSTEM_PROMPT_WITH_SEQ_THINKING if tool_args.get("sequential_thinking", False) else SYSTEM_PROMPT,
        client=client,
        tools=tools,
        workspace_manager=workspace_manager,
        message_queue=queue,
        logger_for_agent_logs=logger_for_agent_logs,
        context_manager=context_manager,
        max_output_tokens_per_turn=MAX_OUTPUT_TOKENS_PER_TURN,
        max_turns=MAX_TURNS,
        websocket=websocket,
        session_id=session_id,
    )
    agent.session_id = session_id
    return agent


def setup_workspace(app, workspace_path):
    try:
        app.mount(
            "/workspace",
            StaticFiles(directory=workspace_path, html=True),
            name="workspace",
        )
    except RuntimeError:
        os.makedirs(workspace_path, exist_ok=True)
        app.mount(
            "/workspace",
            StaticFiles(directory=workspace_path, html=True),
            name="workspace",
        )


def main():
    global global_args
    parser = argparse.ArgumentParser(description="WebSocket Server for interacting with the Agent")
    parser = parse_common_args(parser)
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()
    global_args = args
    setup_workspace(app, args.workspace)
    logger.info(f"Starting WebSocket server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


@app.get("/api/sessions/{device_id}")
async def get_sessions_by_device_id(device_id: str):
    try:
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            query = text("""
            SELECT 
                s.id AS session_id,
                s.workspace_dir,
                s.created_at,
                s.device_id,
                (SELECT e.event_payload FROM event e WHERE e.session_id = s.id AND e.event_type = 'user_message' ORDER BY e.timestamp ASC LIMIT 1) AS first_message
            FROM session s
            WHERE s.device_id = :device_id
            ORDER BY s.created_at DESC
            """)
            result = session.execute(query, {"device_id": device_id})
            sessions = []
            for row in result:
                first_message_payload = json.loads(row.first_message) if row.first_message else {}
                sessions.append({
                    "id": row.session_id,
                    "workspace_dir": row.workspace_dir,
                    "created_at": row.created_at.isoformat(),
                    "device_id": row.device_id,
                    "first_message": first_message_payload.get("content", {}).get("text", ""),
                })
            return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Error retrieving sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving sessions: {str(e)}")


@app.get("/api/sessions/{session_id}/events")
async def get_session_events(session_id: str):
    try:
        db_manager = DatabaseManager()
        with db_manager.get_session() as session:
            events = (
                session.query(Event)
                .filter(Event.session_id == session_id)
                .order_by(asc(Event.timestamp))
                .all()
            )
            event_list = [
                {
                    "id": e.id,
                    "session_id": e.session_id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "event_payload": e.event_payload,
                    "workspace_dir": e.session.workspace_dir,
                }
                for e in events
            ]
            return {"events": event_list}
    except Exception as e:
        logger.error(f"Error retrieving events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving events: {str(e)}")


if __name__ == "__main__":
    main()
