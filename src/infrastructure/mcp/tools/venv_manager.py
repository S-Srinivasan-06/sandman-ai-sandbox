"""MCP tools for virtual environment management inside sandboxes."""
from mcp.server.fastmcp import FastMCP
from src.infrastructure.docker.executor import run_in_container
from src.infrastructure.config import settings
from src.utils.validation import sanitize_packages


def register_venv_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def create_venv_tool(sandbox_id: str, venv_name: str = "default") -> dict:
        """Create a Python virtual environment inside the sandbox at /workspace/.venvs/{venv_name}."""
        safe_name = "".join(c for c in venv_name if c.isalnum() or c in "_-")
        if not safe_name:
            safe_name = "default"
        cmd = ["python", "-m", "venv", f"/workspace/.venvs/{safe_name}"]
        return run_in_container(sandbox_id, cmd, timeout=60).__dict__

    @mcp.tool()
    def install_in_venv_tool(
        sandbox_id: str, venv_name: str, packages: list[str]
    ) -> dict:
        """Install packages into a named virtual environment."""
        if not packages:
            return {"exit_code": 0, "stdout": "No packages specified.", "stderr": ""}

        safe_packages = sanitize_packages(packages)
        if not safe_packages:
            return {"exit_code": 1, "stdout": "", "stderr": "Invalid or empty package list."}

        safe_name = "".join(c for c in venv_name if c.isalnum() or c in "_-") or "default"
        pkg_str = " ".join(safe_packages)
        pip_path = f"/workspace/.venvs/{safe_name}/bin/pip"
        cmd = [
            "bash",
            "-c",
            f"mkdir -p /workspace/.tmp && TMPDIR=/workspace/.tmp {pip_path} install --no-cache-dir {pkg_str}",
        ]
        return run_in_container(sandbox_id, cmd, timeout=settings.DEP_INSTALL_TIMEOUT).__dict__

    @mcp.tool()
    def list_venvs_tool(sandbox_id: str) -> dict:
        """List all virtual environments in the sandbox workspace."""
        cmd = ["bash", "-c", "ls -1 /workspace/.venvs/ 2>/dev/null || echo 'No venvs found.'"]
        return run_in_container(sandbox_id, cmd, timeout=10).__dict__
