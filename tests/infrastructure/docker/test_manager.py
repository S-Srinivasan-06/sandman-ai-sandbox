import pytest
from unittest.mock import MagicMock, patch
from src.infrastructure.docker.manager import create_sandbox, destroy_sandbox


def test_create_sandbox_network_disabled(mock_docker_client, tmp_workspace, monkeypatch):
    monkeypatch.setattr("src.infrastructure.docker.manager.settings.WORKSPACE_BASE", tmp_workspace)
    mock_container = MagicMock()
    mock_container.id = "c123"
    mock_docker_client.containers.run.return_value = mock_container

    res = create_sandbox("python", allow_network=False)
    assert res["sandbox_id"] == "c123"
    assert res["network_enabled"] is False
    call_kwargs = mock_docker_client.containers.run.call_args[1]
    assert call_kwargs["network_disabled"] is True


def test_create_sandbox_network_enabled(mock_docker_client, tmp_workspace, monkeypatch):
    monkeypatch.setattr("src.infrastructure.docker.manager.settings.WORKSPACE_BASE", tmp_workspace)
    mock_container = MagicMock()
    mock_container.id = "c456"
    mock_docker_client.containers.run.return_value = mock_container

    res = create_sandbox("python", allow_network=True)
    assert res["network_enabled"] is True
    call_kwargs = mock_docker_client.containers.run.call_args[1]
    assert call_kwargs["network_disabled"] is False
    assert call_kwargs["dns"] == ["8.8.8.8", "1.1.1.1"]
    assert call_kwargs["sysctls"] == {"net.ipv6.conf.all.disable_ipv6": "1"}


def test_destroy_sandbox(mock_docker_client, tmp_workspace, monkeypatch):
    monkeypatch.setattr("src.infrastructure.docker.manager.settings.WORKSPACE_BASE", tmp_workspace)
    mock_container = MagicMock()
    mock_docker_client.containers.get.return_value = mock_container

    # Create dummy session dir
    sess_dir = tmp_workspace / "sess1"
    sess_dir.mkdir()

    res = destroy_sandbox("c123", "sess1")
    assert res == "Sandbox destroyed"
    mock_container.stop.assert_called_once_with(timeout=5)
    assert not sess_dir.exists()
