"""MCP tools for session-scoped environment variable management."""
import json
import re
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from src.infrastructure.config import settings
from src.utils.validation import safe_workspace_path

def register_env_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def set_env_vars_tool(session_id: str, variables: dict[str, str]) -> str:
        """Set or update environment variables for a sandbox session. Secrets are redacted in logs."""
        if not variables:
            return "No variables provided."
        
        # Validate keys (alphanumeric + underscore)
        safe_vars = {}
        for k, v in variables.items():
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", k):
                safe_vars[k] = str(v)
        
        if not safe_vars:
            return "Invalid variable names. Use alphanumeric + underscore only."

        env_path = safe_workspace_path(settings.WORKSPACE_BASE, session_id, ".env.session")
        existing = {}
        if env_path.exists():
            try:
                existing = json.loads(env_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        existing.update(safe_vars)
        env_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        
        # Redact sensitive-looking values in response
        redacted = {k: ("***REDACTED***" if re.search(r"(key|token|secret|password|api)", k, re.I) else v) 
                    for k, v in safe_vars.items()}
        return f"Updated {len(safe_vars)} environment variables: {json.dumps(redacted)}"

    @mcp.tool()
    def get_env_vars_tool(session_id: str) -> str:
        """Retrieve current session environment variables (secrets redacted)."""
        env_path = safe_workspace_path(settings.WORKSPACE_BASE, session_id, ".env.session")
        if not env_path.exists():
            return "No environment variables set for this session."
        
        try:
            data = json.loads(env_path.read_text(encoding="utf-8"))
            redacted = {k: ("***REDACTED***" if re.search(r"(key|token|secret|password|api)", k, re.I) else v) 
                        for k, v in data.items()}
            return json.dumps(redacted, indent=2)
        except Exception as e:
            return f"Failed to read env vars: {e}"
