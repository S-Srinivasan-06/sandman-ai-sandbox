"""Docker command executor with timeout handling & structured output."""

import docker
import shlex
from dataclasses import dataclass
from src.infrastructure.config import settings
from src.utils.errors import SandboxError

from src.infrastructure.docker.manager import get_client


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float | None = None


def run_in_container(
    sandbox_id: str, command: str | list[str], timeout: int | None = None
) -> ExecutionResult:
    """Execute a command inside a sandbox container with strict timeout enforcement."""
    timeout_val = timeout or settings.EXEC_TIMEOUT
    cmd_list = ["timeout", str(timeout_val)] + (
        command if isinstance(command, list) else shlex.split(command)
    )

    try:
        container = get_client().containers.get(sandbox_id)
        exit_code, output = container.exec_run(cmd_list, demux=True, user=settings.SANDBOX_USER)
        stdout = output[0].decode("utf-8", errors="replace") if output[0] else ""
        stderr = output[1].decode("utf-8", errors="replace") if output[1] else ""
        return ExecutionResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
    except docker.errors.NotFound as e:
        raise SandboxError(f"Container {sandbox_id} not found: {e}") from e
    except docker.errors.APIError as e:
        err_msg = str(e).lower()
        if "not running" in err_msg or "no such container" in err_msg:
            return ExecutionResult(
                exit_code=-1, stdout="", stderr=f"Container unavailable: {e.explanation}"
            )
        raise SandboxError(f"Execution failed: {e}") from e
    except Exception as e:
        err_msg = str(e).lower()
        if "timeout" in err_msg:
            return ExecutionResult(
                exit_code=137, stdout="", stderr=f"Execution timed out after {timeout_val}s"
            )
        raise SandboxError(f"Execution failed: {e}") from e
