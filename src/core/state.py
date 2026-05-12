"""LangGraph agent state schema."""

from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    sandbox_id: str
    session_id: str
    network_enabled: bool
    attempt_count: int
    last_error: str
    target_file: str
    test_file: str
    status: str  # "running" | "retrying" | "success" | "failed" | "done"
    session_start_time: float  # Unix timestamp
    time_budget_minutes: int
    persistent_session: bool
    active_venv: str
    custom_image: str
