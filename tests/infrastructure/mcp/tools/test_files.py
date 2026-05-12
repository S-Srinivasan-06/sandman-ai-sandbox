import pytest
from pathlib import Path
from src.infrastructure.mcp.tools.files import write_file_tool, read_file_tool


def test_write_and_read_file(tmp_workspace, monkeypatch):
    monkeypatch.setattr("src.infrastructure.mcp.tools.files.settings.WORKSPACE_BASE", tmp_workspace)

    write_file_tool("sess1", "test.txt", "hello world")
    assert (tmp_workspace / "sess1" / "test.txt").read_text() == "hello world"

    res = read_file_tool("sess1", "test.txt")
    assert res == "hello world"
