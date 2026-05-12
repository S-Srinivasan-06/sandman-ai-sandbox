"""MCP tool for dry-run syntax/lint checking inside the sandbox."""
from mcp.server.fastmcp import FastMCP
from src.infrastructure.docker.executor import run_in_container
from src.infrastructure.config import settings

def register_linter_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def lint_file_tool(sandbox_id: str, filename: str, language: str = "python") -> dict:
        """Run syntax/dry-run checks without full execution. Saves time & tokens on obvious errors."""
        lang = language.lower()
        if lang == "python":
            cmd = ["python", "-m", "py_compile", filename]
        elif lang == "node":
            cmd = ["node", "--check", filename]
        elif lang == "go":
            cmd = ["go", "vet", filename]
        else:
            return {"exit_code": 1, "stdout": "", "stderr": f"Unsupported language for linting: {lang}"}

        result = run_in_container(sandbox_id, cmd, timeout=30)
        return {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "check_type": "syntax_lint"
        }
