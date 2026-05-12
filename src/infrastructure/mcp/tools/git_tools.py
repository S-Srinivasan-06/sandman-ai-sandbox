"""MCP tools for Git repository management inside sandboxes."""
import re
from mcp.server.fastmcp import FastMCP
from src.infrastructure.docker.executor import run_in_container
from src.utils.validation import safe_workspace_path
from src.infrastructure.config import settings

ALLOWED_GIT_HOSTS = re.compile(r"^https://(github\.com|gitlab\.com|bitbucket\.org|[\w\-]+\.github\.io)/")

def register_git_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def git_clone_tool(sandbox_id: str, session_id: str, repo_url: str, target_dir: str = "repo") -> dict:
        """Clone a Git repository into the workspace. Only allows trusted hosts."""
        if not ALLOWED_GIT_HOSTS.match(repo_url):
            return {"exit_code": 1, "stdout": "", "stderr": "Blocked: Only GitHub/GitLab/Bitbucket HTTPS URLs allowed."}
        
        safe_dir = re.sub(r"[^\w\-\.]", "", target_dir) or "repo"
        # In a real setup, we'd ensure target_dir is inside /workspace
        cmd = ["git", "clone", "--depth", "1", repo_url, safe_dir]
        return run_in_container(sandbox_id, cmd, timeout=120).__dict__

    @mcp.tool()
    def git_commit_tool(sandbox_id: str, session_id: str, repo_dir: str, message: str) -> dict:
        """Stage & commit changes in a workspace repository."""
        safe_dir = re.sub(r"[^\w\-\.]", "", repo_dir)
        cmd = ["bash", "-c", f"cd {safe_dir} && git add -A && git commit -m {repr(message)}"]
        return run_in_container(sandbox_id, cmd, timeout=30).__dict__

    @mcp.tool()
    def git_push_tool(sandbox_id: str, session_id: str, repo_dir: str) -> dict:
        """Push commits to remote. Requires GIT_TOKEN or SSH key set via env manager."""
        safe_dir = re.sub(r"[^\w\-\.]", "", repo_dir)
        cmd = ["bash", "-c", f"cd {safe_dir} && git push origin HEAD"]
        return run_in_container(sandbox_id, cmd, timeout=60).__dict__
