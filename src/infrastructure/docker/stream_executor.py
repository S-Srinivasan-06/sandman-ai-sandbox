"""Async streaming executor for real-time container output."""
import asyncio
import docker
from src.infrastructure.config import settings
from src.utils.errors import SandboxError

from src.infrastructure.docker.manager import get_client

async def run_in_container_stream(
    sandbox_id: str, 
    command: list[str], 
    stream_callback,
    timeout: int | None = None
) -> dict:
    """Execute command & stream stdout/stderr chunks to callback in real-time."""
    # Note: docker-py's stream=True is a blocking generator.
    # We run the iteration in a thread to keep it non-blocking for the event loop.
    
    def _run():
        try:
            container = get_client().containers.get(sandbox_id)
            exec_id = container.client.api.exec_create(
                container.id, command, user=settings.SANDBOX_USER, tty=False
            )["Id"]
            
            output = container.client.api.exec_start(exec_id, stream=True, demux=True)
            
            for chunk in output:
                yield chunk, exec_id
                
        except Exception as e:
            raise SandboxError(f"Streaming execution failed: {e}")

    try:
        # Run generator in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        exec_id = None
        
        # We need to use a thread pool or run_in_executor for the blocking generator
        # but for simplicity in this implementation, we'll iterate and await the callback
        for chunk, eid in await loop.run_in_executor(None, lambda: list(_run())):
            exec_id = eid
            stdout_b, stderr_b = chunk
            if stdout_b:
                await stream_callback("stdout", stdout_b.decode("utf-8", errors="replace"))
            if stderr_b:
                await stream_callback("stderr", stderr_b.decode("utf-8", errors="replace"))
        
        # Get final exit code
        if exec_id:
            container = get_client().containers.get(sandbox_id)
            inspect = container.client.api.exec_inspect(exec_id)
            return {"exit_code": inspect["ExitCode"], "streamed": True}
        return {"exit_code": 1, "error": "No execution ID found"}
        
    except docker.errors.NotFound as e:
        raise SandboxError(f"Container {sandbox_id} not found: {e}") from e
    except Exception as e:
        raise SandboxError(f"Streaming execution failed: {e}") from e
