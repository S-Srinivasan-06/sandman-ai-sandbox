"""Test LangGraph node functions directly (faster & more reliable than full graph compilation)."""

import pytest
import time
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.core.state import AgentState
from src.core.graph import should_continue, check_result_node, finalize_node


def _make_state(**overrides) -> AgentState:
    """Helper to build a valid AgentState with all required fields."""
    defaults = dict(
        messages=[],
        sandbox_id="",
        session_id="",
        network_enabled=False,
        attempt_count=0,
        last_error="",
        target_file="",
        test_file="",
        status="running",
        session_start_time=time.time(),
        time_budget_minutes=30,
        persistent_session=False,
        active_venv="",
        custom_image="",
    )
    defaults.update(overrides)
    return AgentState(**defaults)


def test_should_continue_routes_to_tools():
    state = _make_state(
        messages=[AIMessage(content="", tool_calls=[{"name": "test", "args": {}, "id": "call_1"}])],
    )
    assert should_continue(state) == "tools"


def test_should_continue_routes_to_finalize():
    state = _make_state(
        messages=[AIMessage(content="Done!")],
    )
    assert should_continue(state) == "finalize"


def test_check_result_node_success():
    tool_content = '{"exit_code": 0, "stdout": "passed", "stderr": ""}'
    state = _make_state(
        messages=[ToolMessage(content=tool_content, tool_call_id="1")],
    )
    res = check_result_node(state)
    assert res["status"] == "success"
    assert res["last_error"] == ""


def test_check_result_node_retry():
    tool_content = '{"exit_code": 1, "stdout": "", "stderr": "SyntaxError"}'
    state = _make_state(
        messages=[ToolMessage(content=tool_content, tool_call_id="1")],
    )
    with patch("src.core.graph.settings.MAX_RETRIES", 3):
        res = check_result_node(state)
    assert res["status"] == "retrying"
    assert res["attempt_count"] == 1


def test_finalize_node_chat_mode():
    state = _make_state(
        messages=[AIMessage(content="Hello!")],
    )
    res = finalize_node(state)
    assert res["status"] == "done"
    assert "messages" not in res  # Chat mode passes through without adding messages
