"""MCP tools for code execution, testing, and dependency installation."""

from mcp.server.fastmcp import FastMCP
from src.infrastructure.docker.executor import run_in_container
from src.infrastructure.config import settings
from src.utils.validation import sanitize_packages
from src.infrastructure.docker.manager import get_client
import shlex


def register_runner_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def run_file_tool(sandbox_id: str, filename: str) -> dict:
        return run_in_container(sandbox_id, ["python", filename]).__dict__

    @mcp.tool()
    def run_tests_tool(sandbox_id: str, test_filename: str) -> dict:
        return run_in_container(
            sandbox_id, ["python", "-m", "pytest", test_filename, "-v"]
        ).__dict__

    @mcp.tool()
    def install_dependencies_tool(
        sandbox_id: str, packages: list[str], manager: str = "pip"
    ) -> dict:
        if not packages:
            return {"exit_code": 0, "stdout": "No packages specified.", "stderr": ""}

        safe_packages = sanitize_packages(packages)
        if not safe_packages:
            return {"exit_code": 1, "stdout": "", "stderr": "Invalid or empty package list."}

        pkg_str = " ".join(shlex.quote(p) for p in safe_packages)

        timeout_val = settings.DEP_INSTALL_TIMEOUT
        # 🔹 Use /workspace/.tmp for pip extraction to avoid 100m tmpfs limit
        if manager == "pip":
            cmd = f"mkdir -p /workspace/.tmp && TMPDIR=/workspace/.tmp timeout {timeout_val} pip install --no-cache-dir {pkg_str}"
        else:
            cmd = f"timeout {timeout_val} apt-get update && apt-get install -y {pkg_str}"

        container = get_client().containers.get(sandbox_id)
        try:
            exec_user = "root" if settings.ALLOW_ROOT_DEP_INSTALL else settings.SANDBOX_USER
            exit_code, output = container.exec_run(cmd, demux=True, user=exec_user)
            return {
                "exit_code": exit_code,
                "stdout": output[0].decode("utf-8", errors="replace") if output[0] else "",
                "stderr": output[1].decode("utf-8", errors="replace") if output[1] else "",
            }
        except Exception as e:
            return {"exit_code": -1, "stdout": "", "stderr": str(e)}
