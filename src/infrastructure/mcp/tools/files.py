"""MCP tools for file operations inside the sandbox workspace."""

from mcp.server.fastmcp import FastMCP
from pathlib import Path
from src.infrastructure.config import settings
import shutil
import re
from src.utils.validation import safe_workspace_path


def write_file_tool(session_id: str, filename: str, content: str) -> str:
    path = safe_workspace_path(settings.WORKSPACE_BASE, session_id, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Written {filename} successfully."


def read_file_tool(session_id: str, filename: str) -> str:
    path = safe_workspace_path(settings.WORKSPACE_BASE, session_id, filename)
    return path.read_text(encoding="utf-8") if path.exists() else f"File not found: {filename}"


def copy_all_files_tool(session_id: str) -> str:
    src = safe_workspace_path(settings.WORKSPACE_BASE, session_id, "")
    dst = settings.OUTPUT_DIR / f"out_{session_id[:8]}"
    dst.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return "Workspace not found."
    n = 0
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)
            n += 1
    return f"Copied {n} files to output directory."


def zip_workspace_tool(session_id: str, zip_name: str = "workspace_bundle") -> str:
    src = safe_workspace_path(settings.WORKSPACE_BASE, session_id, "")
    dst = settings.OUTPUT_DIR
    dst.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        return "Workspace not found."

    safe_zip_name = re.sub(r"[^a-zA-Z0-9_\-]", "", zip_name)
    if not safe_zip_name:
        safe_zip_name = "workspace_bundle"

    shutil.make_archive(str(dst / f"{safe_zip_name}_{session_id[:8]}"), "zip", src)
    return f"Zipped workspace successfully."


def register_file_tools(mcp: FastMCP) -> None:
    mcp.tool()(write_file_tool)
    mcp.tool()(read_file_tool)
    mcp.tool()(copy_all_files_tool)
    mcp.tool()(zip_workspace_tool)
