"""MCP tool for secure, depth-limited workspace file exploration."""
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from src.infrastructure.config import settings
from src.utils.validation import safe_workspace_path

def register_explorer_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def list_files_tool(session_id: str, target_path: str = ".", max_depth: int = 3) -> str:
        """List workspace files as a tree. Enforces depth limits & path traversal protection."""
        max_depth = max(1, min(max_depth, 5))  # Clamp between 1-5
        base = safe_workspace_path(settings.WORKSPACE_BASE, session_id, target_path)
        
        if not base.exists():
            return f"Path not found: {target_path}"
        if not base.is_dir():
            return f"Path is a file: {target_path}"

        tree_lines = []
        def _walk(current: Path, prefix: str, depth: int):
            if depth > max_depth:
                tree_lines.append(f"{prefix}└── ... (max depth reached)")
                return
            try:
                items = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except (PermissionError, OSError):
                # OSError catches WinError 1920 and other reparse point issues
                tree_lines.append(f"{prefix}└── [Inaccessible]")
                return

            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                try:
                    is_dir = item.is_dir()
                    suffix = "/" if is_dir else ""
                    tree_lines.append(f"{prefix}{connector}{item.name}{suffix}")
                    
                    if is_dir:
                        extension = "    " if is_last else "│   "
                        _walk(item, prefix + extension, depth + 1)
                except (PermissionError, OSError):
                    tree_lines.append(f"{prefix}{connector}{item.name} [Inaccessible]")

        tree_lines.append(f"{base.name}/")
        _walk(base, "", 1)
        return "\n".join(tree_lines)
