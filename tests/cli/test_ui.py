import pytest
import asyncio
from src.cli.ui import StreamManager


@pytest.mark.asyncio
async def test_stream_manager_log_methods():
    """Verify all StreamManager log methods execute without errors."""
    manager = StreamManager()

    # These methods print to console; verify they don't raise
    await manager.log_tool_call("test_tool", {"arg": "value"})
    await manager.log_tool_result("success")
    await manager.log_tool_result('{"exit_code": 0, "stdout": "ok", "stderr": ""}')
    await manager.log_ai("hello from AI")
    await manager.log_system("system message")


@pytest.mark.asyncio
async def test_stream_manager_clear():
    """Verify clear doesn't raise."""
    manager = StreamManager()
    manager.clear()  # Should not raise
