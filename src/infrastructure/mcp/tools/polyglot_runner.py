"""MCP tool for multi-language script execution inside sandboxes."""
import re
from mcp.server.fastmcp import FastMCP
from src.infrastructure.docker.executor import run_in_container
from src.infrastructure.config import LANGUAGE_CONFIG, settings

EXT_TO_LANG = {
    ".py": "python", ".js": "node", ".ts": "node", ".go": "go",
    ".sh": "bash", ".rs": "rust", ".rb": "ruby"
}

def register_polyglot_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def run_polyglot_tool(sandbox_id: str, filename: str, language: str | None = None) -> dict:
        """Run a script using the correct interpreter based on extension or explicit language."""
        ext_match = re.search(r"\.[a-z]+$", filename.lower())
        lang = language or (EXT_TO_LANG.get(ext_match.group()) if ext_match else "python")
        
        cfg = LANGUAGE_CONFIG.get(lang)
        if not cfg:
            return {"exit_code": 1, "stdout": "", "stderr": f"Unsupported language: {lang}"}
        
        cmd = cfg["run_cmd"].format(file=filename).split()
        return run_in_container(sandbox_id, cmd, timeout=settings.EXEC_TIMEOUT).__dict__
    @mcp.tool()
    def run_command_tool(sandbox_id: str, command: str, timeout: int = 600) -> dict:
        """Run a raw shell command inside the sandbox. Use for venv execution (e.g. /workspace/.venvs/myenv/bin/python main.py)."""
        cmd = ["bash", "-c", command]
        return run_in_container(sandbox_id, cmd, timeout=timeout).__dict__
