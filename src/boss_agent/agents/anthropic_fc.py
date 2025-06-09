import asyncio
import logging
import os
from typing import Any, Optional, Dict
import uuid

from typing import List
from fastapi import WebSocket
from boss_agent.agents.base import BaseAgent
from boss_agent.core.event import EventType, RealtimeEvent
from boss_agent.llm.base import LLMClient, TextResult, ToolCallParameters, TextPrompt
from boss_agent.llm.context_manager.base import ContextManager
from boss_agent.llm.message_history import MessageHistory
from boss_agent.tools.base import ToolImplOutput, LLMTool
from boss_agent.tools.utils import encode_image
from boss_agent.db.manager import DatabaseManager
from boss_agent.tools import AgentToolManager
from boss_agent.utils.constants import COMPLETE_MESSAGE, DEFAULT_MODEL
from boss_agent.utils.workspace_manager import WorkspaceManager
from boss_agent.llm.gemini import GeminiDirectClient

TOOL_RESULT_INTERRUPT_MESSAGE = "Tool execution interrupted by user."
AGENT_INTERRUPT_MESSAGE = "Agent interrupted by user."
TOOL_CALL_INTERRUPT_FAKE_MODEL_RSP = (
    "Tool execution interrupted by user. You can resume by providing a new instruction."
)
AGENT_INTERRUPT_FAKE_MODEL_RSP = (
    "Agent interrupted by user. You can resume by providing a new instruction."
)


class AnthropicFC(BaseAgent):
    name = "general_agent"
    description = """\
A general agent that can accomplish tasks and answer questions.

If you are faced with a task that involves more than a few steps, or if the task is complex, or if the instructions are very long,
try breaking down the task into smaller steps. After call this tool to update or create a plan, use write_file or str_replace_tool to update the plan to todo.md
"""
    input_schema = {
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "The instruction to the agent.",
            },
        },
        "required": ["instruction"],
    }
    websocket: Optional[WebSocket]

    def __init__(
        self,
        system_prompt: str,
        client: LLMClient,
        tools: List[LLMTool],
        workspace_manager: WorkspaceManager,
        message_queue: asyncio.Queue,
        logger_for_agent_logs: logging.Logger,
        context_manager: ContextManager,
        max_output_tokens_per_turn: int = 8192,
        max_turns: int = 10,
        websocket: Optional[WebSocket] = None,
        session_id: Optional[uuid.UUID] = None,
        interactive_mode: bool = True,
        use_gemini: bool = True,
    ):
        """Initialize the agent."""
        super().__init__()
        self.workspace_manager = workspace_manager
        self.system_prompt = system_prompt
        
        if use_gemini and os.getenv("GEMINI_API_KEY"):
            self.client = GeminiDirectClient(model_name=DEFAULT_MODEL)
        else:
            self.client = client
            
        self.tool_manager = AgentToolManager(
            tools=tools,
            logger_for_agent_logs=logger_for_agent_logs,
            interactive_mode=interactive_mode,
        )

        self.logger_for_agent_logs = logger_for_agent_logs
        self.max_output_tokens = max_output_tokens_per_turn
        self.max_turns = max_turns

        self.interrupted = False
        self.history = MessageHistory(context_manager)
        self.session_id = session_id

        self.db_manager = DatabaseManager()

        self.message_queue = message_queue
        self.websocket = websocket

    async def _process_messages(self):
        try:
            while True:
                try:
                    message: RealtimeEvent = await self.message_queue.get()

                    if self.session_id is not None:
                        self.db_manager.save_event(self.session_id, message)
                    else:
                        self.logger_for_agent_logs.info(
                            f"No session ID, skipping event: {message}"
                        )

                    if (
                        message.type != EventType.USER_MESSAGE
                        and self.websocket is not None
                    ):
                        try:
                            await self.websocket.send_json(message.model_dump())
                        except Exception as e:
                            self.logger_for_agent_logs.warning(
                                f"Failed to send message to websocket: {str(e)}"
                            )
                            self.websocket = None

                    self.message_queue.task_done()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger_for_agent_logs.error(
                        f"Error processing WebSocket message: {str(e)}"
                    )
        except asyncio.CancelledError:
            self.logger_for_agent_logs.info("Message processor stopped")
        except Exception as e:
            self.logger_for_agent_logs.error(f"Error in message processor: {str(e)}")

    def _validate_tool_parameters(self):
        """Validate tool parameters and check for duplicates."""
        tool_params = [tool.get_tool_param() for tool in self.tool_manager.get_tools()]
        tool_names = [param.name for param in tool_params]
        sorted_names = sorted(tool_names)
        for i in range(len(sorted_names) - 1):
            if sorted_names[i] == sorted_names[i + 1]:
                raise ValueError(f"Tool {sorted_names[i]} is duplicated")
        return tool_params

    def start_message_processing(self):
        """Start processing the message queue."""
        return asyncio.create_task(self._process_messages())

    def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
        tool_choice: Optional[Dict[str, Any]] = None,
    ) -> ToolImplOutput:
        instruction = tool_input["instruction"]
        files = tool_input["files"]

        user_input_delimiter = "-" * 45 + " USER INPUT " + "-" * 45 + "\n" + instruction
        self.logger_for_agent_logs.info(f"\n{user_input_delimiter}\n")

        image_blocks = []
        if files:
            instruction = f"""{instruction}\n\nAttached files:\n"""
            for file in files:
                relative_path = self.workspace_manager.relative_path(file)
                instruction += f" - {relative_path}\n"
                self.logger_for_agent_logs.info(f"Attached file: {relative_path}")

            for file in files:
                ext = file.split(".")[-1]
                if ext == "jpg":
                    ext = "jpeg"
                if ext in ["png", "gif", "jpeg", "webp"]:
                    base64_image = encode_image(
                        str(self.workspace_manager.workspace_path(file))
                    )
                    image_blocks.append(
                        {
                            "source": {
                                "type": "base64",
                                "media_type": f"image/{ext}",
                                "data": base64_image,
                            }
                        }
                    )

        self.history.add_user_prompt(instruction, image_blocks)
        self.interrupted = False

        remaining_turns = self.max_turns
        while remaining_turns > 0:
            self.history.truncate()
            remaining_turns -= 1

            delimiter = "-" * 45 + " NEW TURN " + "-" * 45
            self.logger_for_agent_logs.info(f"\n{delimiter}\n")

            all_tool_params = self._validate_tool_parameters()

            if self.interrupted:
                self.add_fake_assistant_turn(AGENT_INTERRUPT_FAKE_MODEL_RSP)
                return ToolImplOutput(
                    tool_output=AGENT_INTERRUPT_MESSAGE,
                    tool_result_message=AGENT_INTERRUPT_MESSAGE,
                )

            self.logger_for_agent_logs.info(
                f"(Current token count: {self.history.count_tokens()})\n"
            )

            response = self.client.generate(
                messages=self.history.get_messages_for_llm(),
                max_tokens=self.max_output_tokens,
                tools=all_tool_params,
                system_prompt=self.system_prompt,
                tool_choice=tool_choice,
            )
            if isinstance(response, tuple):
                model_response, _ = response
            else:
                model_response = response

            if len(model_response) == 0:
                model_response = [TextResult(text=COMPLETE_MESSAGE)]

            self.history.add_assistant_turn(model_response)

            pending_tool_calls = self.history.get_pending_tool_calls()

            if len(pending_tool_calls) == 0:
                self.logger_for_agent_logs.info("[no tools were called, forcing tool use]")
                self.history.add_user_prompt("You must use a tool to answer the question.")
                continue

            if len(pending_tool_calls) > 1:
                raise ValueError("Only one tool call per turn is supported")

            assert len(pending_tool_calls) == 1

            tool_call = pending_tool_calls[0]

            self.message_queue.put_nowait(
                RealtimeEvent(
                    type=EventType.TOOL_CALL,
                    content={
                        "tool_call_id": tool_call.tool_call_id,
                        "tool_name": tool_call.tool_name,
                        "tool_input": tool_call.tool_input,
                    },
                )
            )

            text_results = [
                item for item in model_response if isinstance(item, TextResult)
            ]
            if len(text_results) > 0:
                text_result = text_results[0]
                self.logger_for_agent_logs.info(
                    f"Top-level agent planning next step: {text_result.text}\n",
                )

            if self.interrupted:
                self.add_tool_call_result(tool_call, TOOL_RESULT_INTERRUPT_MESSAGE)
                self.add_fake_assistant_turn(TOOL_CALL_INTERRUPT_FAKE_MODEL_RSP)
                return ToolImplOutput(
                    tool_output=TOOL_RESULT_INTERRUPT_MESSAGE,
                    tool_result_message=TOOL_RESULT_INTERRUPT_MESSAGE,
                )
            tool_result = self.tool_manager.run_tool(tool_call, self.history)

            self.add_tool_call_result(tool_call, tool_result)

            # --- Add Session Summary ---
            summary_prompt = f"Based on the result of the tool call '{tool_call.tool_name}' which returned '{str(tool_result)[:200]}...', what is the single most important new piece of information or confirmation you have learned? State it as a brief, factual summary."
            summary_response = self.client.generate(
                messages=[[TextPrompt(text=summary_prompt)]],
                max_tokens=100,
            )
            if isinstance(summary_response, tuple) and len(summary_response[0]) > 0:
                summary_text = summary_response[0][0].text
                self.history.add_session_summary(f"Summary of last action: {summary_text}")
            if self.tool_manager.should_stop():
                self.add_fake_assistant_turn(self.tool_manager.get_final_answer())
                return ToolImplOutput(
                    tool_output=self.tool_manager.get_final_answer(),
                    tool_result_message="Task completed",
                )

        agent_answer = "Agent did not complete after max turns"
        self.message_queue.put_nowait(
            RealtimeEvent(type=EventType.AGENT_RESPONSE, content={"text": agent_answer})
        )
        return ToolImplOutput(
            tool_output=agent_answer, tool_result_message=agent_answer
        )

    def get_tool_start_message(self, tool_input: dict[str, Any]) -> str:
        return f"Agent started with instruction: {tool_input['instruction']}"

    def run_agent(
        self,
        instruction: str,
        files: list[str] | None = None,
        resume: bool = False,
        tool_choice: Optional[Dict[str, Any]] = None,
        orientation_instruction: str | None = None,
    ) -> ToolImplOutput:
        """Start a new agent run."""
        self.tool_manager.reset()
        if not resume:
            self.history.clear()
            self.interrupted = False

        tool_input = {
            "instruction": instruction,
            "files": files,
        }
        if orientation_instruction:
            tool_input["orientation_instruction"] = orientation_instruction
        result = self.run_impl(tool_input, self.history, tool_choice=tool_choice)
        return result

    def clear(self):
        """Clear the dialog and reset interruption state."""
        self.history.clear()
        self.interrupted = False

    def cancel(self):
        """Cancel the agent execution."""
        self.interrupted = True
        self.logger_for_agent_logs.info("Agent cancellation requested")

    def add_tool_call_result(self, tool_call: ToolCallParameters, tool_result: str):
        """Add a tool call result to the history and send it to the message queue."""
        self.history.add_tool_call_result(tool_call, tool_result)

        self.message_queue.put_nowait(
            RealtimeEvent(
                type=EventType.TOOL_RESULT,
                content={
                    "tool_call_id": tool_call.tool_call_id,
                    "tool_name": tool_call.tool_name,
                    "result": tool_result,
                },
            )
        )

    def add_fake_assistant_turn(self, text: str):
        """Add a fake assistant turn to the history and send it to the message queue."""
        self.history.add_assistant_turn([TextResult(text=text)])
        if self.interrupted:
            rsp_type = EventType.AGENT_RESPONSE_INTERRUPTED
        else:
            rsp_type = EventType.AGENT_RESPONSE

        self.message_queue.put_nowait(
            RealtimeEvent(
                type=rsp_type,
                content={"text": text},
            )
        )
