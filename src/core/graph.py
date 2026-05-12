"""LangGraph state machine: agent → tools → check → retry/finalize → cleanup → END"""

import json, asyncio, os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from .state import AgentState
from .prompt import SYSTEM_PROMPT
from .retry import build_retry_prompt
from .output import package_output
from src.infrastructure.config import settings
from src.infrastructure.docker.manager import destroy_sandbox
import logging

logger = logging.getLogger("sandman")


def should_continue(state: AgentState) -> str:
    last = state["messages"][-1]
    return "tools" if (hasattr(last, "tool_calls") and last.tool_calls) else "finalize"


def check_result_node(state: AgentState) -> AgentState:
    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    updates = {}
    for msg in tool_msgs:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if "sandbox_id" in content:
            try:
                data = json.loads(content)
                updates["sandbox_id"] = data["sandbox_id"]
                updates["session_id"] = data["session_id"]
                updates["network_enabled"] = data.get("network_enabled", False)
            except:
                pass

    if not tool_msgs:
        return {**updates, "status": "retrying", "attempt_count": state.get("attempt_count", 0) + 1}
    try:
        data = (
            json.loads(tool_msgs[-1].content)
            if isinstance(tool_msgs[-1].content, str)
            else tool_msgs[-1].content
        )
        if not isinstance(data, dict) or "exit_code" not in data:
            return {**updates, "status": "running"}
        exit_code, stderr = data.get("exit_code", -1), data.get("stderr", "")
    except:
        return {**updates, "status": "running"}

    if exit_code == 0 and (
        "passed" in str(tool_msgs[-1].content).lower()
        or "test" not in str(tool_msgs[-1].content).lower()
    ):
        return {**updates, "status": "success", "last_error": ""}

    attempt = state.get("attempt_count", 0) + 1
    if attempt >= settings.MAX_RETRIES:
        return {**updates, "status": "failed", "last_error": stderr, "attempt_count": attempt}
    return {**updates, "status": "retrying", "last_error": stderr, "attempt_count": attempt}


def retry_node(state: AgentState) -> AgentState:
    prompt = build_retry_prompt(
        state["messages"][0].content,
        state["last_error"],
        state["attempt_count"],
        settings.MAX_RETRIES,
    )
    return {"messages": [HumanMessage(content=prompt)]}


def finalize_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
        return {"status": "done"}
    if state.get("status") == "success":
        result = package_output(state["session_id"], state.get("target_file", "main.py"))
        return {"messages": [AIMessage(content=result)], "status": "done"}
    return {
        "messages": [
            AIMessage(
                content=f"Failed after {state.get('attempt_count',0)} attempts: {state.get('last_error','Unknown')}"
            )
        ],
        "status": "done",
    }


async def cleanup_node(state: AgentState) -> AgentState:
    if state.get("sandbox_id") and state.get("session_id"):
        await asyncio.to_thread(destroy_sandbox, state["sandbox_id"], state["session_id"])
    if settings.ENABLE_OLLAMA_VRAM_CLEANUP:
        try:
            import requests

            await asyncio.to_thread(
                requests.post,
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={"model": os.getenv("OLLAMA_MODEL", "llama3.1"), "keep_alive": 0},
                timeout=5,
            )
        except Exception:
            pass
    return {}


def create_code_agent_graph(tools, llm):
    llm_with_tools = llm.bind_tools(tools)

    def _handle_tool_error(e: Exception) -> str:
        """Convert tool/validation errors into recoverable LLM messages."""
        return f"Tool execution failed: {str(e)}. Check required arguments (especially session_id/sandbox_id) and retry."

    tool_node = ToolNode(tools, handle_tool_errors=_handle_tool_error)

    def agent_node(state: AgentState) -> AgentState:
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        return {"messages": [llm_with_tools.invoke(messages)]}

    wf = StateGraph(AgentState)
    wf.add_node("agent", agent_node)
    wf.add_node("tools", tool_node)
    wf.add_node("check", check_result_node)
    wf.add_node("retry", retry_node)
    wf.add_node("finalize", finalize_node)
    wf.add_node("cleanup", cleanup_node)
    wf.set_entry_point("agent")
    wf.add_conditional_edges("agent", should_continue, {"tools": "tools", "finalize": "finalize"})
    wf.add_edge("tools", "check")
    wf.add_conditional_edges(
        "check",
        lambda s: s["status"],
        {"success": "finalize", "retrying": "retry", "failed": "finalize", "running": "agent"},
    )
    wf.add_edge("retry", "agent")
    wf.add_edge("finalize", "cleanup")
    wf.add_edge("cleanup", END)
    return wf.compile()
