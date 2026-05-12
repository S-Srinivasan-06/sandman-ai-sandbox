"""MCP FastMCP server initialization & tool registration."""

from mcp.server.fastmcp import FastMCP
from .tools.sandbox import register_sandbox_tools
from .tools.files import register_file_tools
from .tools.runner import register_runner_tools
from .tools.env_manager import register_env_tools
from .tools.file_explorer import register_explorer_tools
from .tools.linter import register_linter_tools
from .tools.time_budget import register_time_budget_tools
from .tools.workspace_manager import register_workspace_tools
from .tools.git_tools import register_git_tools
from .tools.image_selector import register_image_tools
from .tools.venv_manager import register_venv_tools
from .tools.polyglot_runner import register_polyglot_tools

mcp = FastMCP("SandboxCodeRunner")
register_sandbox_tools(mcp)
register_file_tools(mcp)
register_runner_tools(mcp)
register_env_tools(mcp)
register_explorer_tools(mcp)
register_linter_tools(mcp)
register_time_budget_tools(mcp)
register_workspace_tools(mcp)
register_git_tools(mcp)
register_image_tools(mcp)
register_venv_tools(mcp)
register_polyglot_tools(mcp)

if __name__ == "__main__":
    mcp.run()
