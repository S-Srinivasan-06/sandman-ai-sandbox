import pytest
from unittest.mock import MagicMock
from src.infrastructure.docker.executor import run_in_container
from src.utils.errors import SandboxError


def test_run_success(mock_docker_client):
    mock_container = MagicMock()
    mock_container.exec_run.return_value = (0, (b"hello", b""))
    mock_docker_client.containers.get.return_value = mock_container

    result = run_in_container("abc123", "echo hello")
    assert result.exit_code == 0
    assert result.stdout == "hello"
    assert result.stderr == ""


def test_run_timeout(mock_docker_client):
    mock_container = MagicMock()
    mock_container.exec_run.side_effect = Exception("timeout occurred")
    mock_docker_client.containers.get.return_value = mock_container

    result = run_in_container("abc123", "sleep 100", timeout=5)
    assert result.exit_code == 137
    assert "timed out" in result.stderr


def test_run_container_not_found(mock_docker_client):
    import docker.errors

    mock_docker_client.containers.get.side_effect = docker.errors.NotFound("gone")

    with pytest.raises(SandboxError, match="not found"):
        run_in_container("missing", "echo hi")
