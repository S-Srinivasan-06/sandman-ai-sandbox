"""MCP tools for persistent workspace management across agent turns."""
import json
import time
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from src.infrastructure.config import settings
from src.infrastructure.docker.manager import get_client
from src.utils.errors import SandboxError
import logging

logger = logging.getLogger("sandman")
SESSION_REGISTRY = settings.WORKSPACE_BASE / ".sessions.json"

def _load_registry() -> dict:
    if SESSION_REGISTRY.exists():
        try: return json.loads(SESSION_REGISTRY.read_text(encoding="utf-8"))
        except Exception: pass
    return {}

def _save_registry(data: dict) -> None:
    SESSION_REGISTRY.write_text(json.dumps(data, indent=2), encoding="utf-8")

def register_workspace_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def pause_sandbox_tool(sandbox_id: str, session_id: str) -> str:
        """Pause a running sandbox to preserve state & resources. Container stays on disk."""
        try:
            container = get_client().containers.get(sandbox_id)
            container.pause()
            reg = _load_registry()
            reg[session_id] = {"sandbox_id": sandbox_id, "status": "paused", "paused_at": time.time()}
            _save_registry(reg)
            return f"Sandbox {sandbox_id[:12]} paused. State preserved."
        except Exception as e:
            raise SandboxError(f"Failed to pause sandbox: {e}") from e

    @mcp.tool()
    def resume_sandbox_tool(session_id: str) -> dict:
        """Resume a paused sandbox. Returns sandbox_id & status."""
        reg = _load_registry()
        if session_id not in reg or reg[session_id]["status"] != "paused":
            return {"error": "No paused session found for this ID."}
        
        sandbox_id = reg[session_id]["sandbox_id"]
        try:
            container = get_client().containers.get(sandbox_id)
            container.unpause()
            reg[session_id]["status"] = "running"
            _save_registry(reg)
            return {"sandbox_id": sandbox_id, "session_id": session_id, "status": "resumed"}
        except Exception as e:
            raise SandboxError(f"Failed to resume sandbox: {e}") from e

    @mcp.tool()
    def list_active_sessions_tool() -> str:
        """List all tracked sandbox sessions (running/paused)."""
        reg = _load_registry()
        if not reg: return "No active or paused sessions."
        lines = [f"{sid[:8]}: {info['status']} (sandbox: {info['sandbox_id'][:12]})" for sid, info in reg.items()]
        return "\n".join(lines)
