"""Async agent runner & MCP client lifecycle."""

import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.core.graph import create_code_agent_graph
from src.core.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from .ui import StreamManager
from src.infrastructure.docker.manager import destroy_sandbox
import logging
import time
from src.infrastructure.config import settings

logger = logging.getLogger("sandman")

async def watch_time_budget(session_id: str, sandbox_id: str, budget_minutes: int, stream: StreamManager) -> None:
    """Background task that destroys sandbox when time budget expires."""
    expiry = time.time() + (budget_minutes * 60)
    while time.time() < expiry:
        await asyncio.sleep(10)
    await stream.log_system(f"⏳ Time budget ({budget_minutes}m) expired. Cleaning up...")
    destroy_sandbox(sandbox_id, session_id)


async def run_agent_turn(messages: list, llm, tools: list, stream: StreamManager) -> list:
    graph = create_code_agent_graph(tools, llm)
    initial_state = AgentState(
        messages=messages,
        sandbox_id="",
        session_id="",
        network_enabled=False,
        attempt_count=0,
        last_error="",
        target_file="main.py",
        test_file="test_main.py",
        status="running",
        session_start_time=time.time(),
        time_budget_minutes=settings.SESSION_TIME_BUDGET_MINUTES,
        persistent_session=settings.ENABLE_PERSISTENT_SANDBOXES,
        active_venv="",
        custom_image="",
    )
    current_messages = list(messages)
    sandbox_id, session_id = "", ""

    try:
        async for event in graph.astream(initial_state, stream_mode="updates"):
            for node_name, update in event.items():
                if isinstance(update, dict):
                    if "sandbox_id" in update:
                        old_sandbox_id = sandbox_id
                        sandbox_id = update["sandbox_id"]
                        if sandbox_id and sandbox_id != old_sandbox_id:
                            budget = update.get("time_budget_minutes", settings.SESSION_TIME_BUDGET_MINUTES)
                            asyncio.create_task(watch_time_budget(session_id, sandbox_id, budget, stream))
                    if "session_id" in update:
                        session_id = update["session_id"]
                if isinstance(update, dict) and "messages" in update:
                    new_msgs = update["messages"]
                    if not new_msgs:
                        continue
                    current_messages.extend(new_msgs)
                    msg = new_msgs[-1]
                    
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            # 📺 Real-time Stream Interception
                            if tc["name"] == "run_file_tool" and tc["args"].get("live_stream"):
                                from src.infrastructure.docker.stream_executor import run_in_container_stream
                                
                                async def chunk_handler(channel: str, text: str):
                                    await stream.log_tool_result(f"[{channel.upper()}] {text.strip()}")
                                
                                await stream.log_tool_call(tc["name"], tc["args"])
                                result = await run_in_container_stream(
                                    sandbox_id, ["python", tc["args"]["filename"]], chunk_handler, timeout=settings.EXEC_TIMEOUT
                                )
                                # Inject result back into graph state as a ToolMessage
                                current_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                                continue
                                
                            await stream.log_tool_call(tc["name"], tc["args"])
                    elif isinstance(msg, ToolMessage):
                        await stream.log_tool_result(msg.content if msg.content else "")
                    elif hasattr(msg, "content") and msg.content and isinstance(msg, AIMessage):
                        await stream.log_ai(msg.content)
        return current_messages
    except KeyboardInterrupt:
        return messages
    except Exception as e:
        await stream.log_system(f"Error: {str(e)[:100]}")
        logger.exception("agent_turn_failed")
        return messages
    finally:
        if sandbox_id:
            await stream.log_system("Cleaning up sandbox...")
            destroy_sandbox(sandbox_id, session_id)
