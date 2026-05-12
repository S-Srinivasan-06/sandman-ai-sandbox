"""Shared pytest fixtures for Sandman test suite."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def mock_docker_client(mocker):
    """Mock docker client globally for infrastructure tests."""
    mock_client = MagicMock()
    mocker.patch("src.infrastructure.docker.manager.get_client", return_value=mock_client)
    mocker.patch("src.infrastructure.docker.executor.get_client", return_value=mock_client)
    return mock_client


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace directory."""
    ws = tmp_path / "sandbox_workspace"
    ws.mkdir()
    return ws


@pytest.fixture
def tmp_outputs(tmp_path: Path) -> Path:
    """Create a temporary outputs directory."""
    out = tmp_path / "outputs"
    out.mkdir()
    return out
