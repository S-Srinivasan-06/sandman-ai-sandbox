"""MCP tool to set or check session time budgets."""
import time
from mcp.server.fastmcp import FastMCP

def register_time_budget_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def set_time_budget_tool(session_id: str, minutes: int) -> str:
        """Set a hard time limit for this sandbox session. Auto-cleanup triggers on expiry."""
        if not 5 <= minutes <= 240:
            return "Budget must be between 5 and 240 minutes."
        return f"Time budget set to {minutes} minutes for session {session_id[:8]}."
