"""MCP tools for sandbox lifecycle."""

from typing import Any
from mcp.server.fastmcp import FastMCP
from src.infrastructure.docker.manager import create_sandbox, destroy_sandbox


def register_sandbox_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def create_sandbox_tool(
        language: str = "python",
        custom_command: Any = None,
        env_vars: Any = None,
        allow_network: bool = False,
    ) -> dict:
        """Create isolated sandbox. Set allow_network=True ONLY for tasks requiring internet."""

        # 🔹 Sanitize LLM hallucinations (LLMs often pass {} or "" instead of null)
        if isinstance(custom_command, dict) and not custom_command:
            custom_command = None
        if isinstance(custom_command, str) and not custom_command.strip():
            custom_command = None

        if isinstance(env_vars, dict) and not env_vars:
            env_vars = None

        return create_sandbox(language, custom_command, env_vars, allow_network)

    @mcp.tool()
    def destroy_sandbox_tool(sandbox_id: str, session_id: str) -> str:
        """Stop container and wipe workspace."""
        return destroy_sandbox(sandbox_id, session_id)
