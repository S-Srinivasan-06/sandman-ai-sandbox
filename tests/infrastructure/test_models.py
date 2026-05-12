import pytest
import requests
from unittest.mock import patch, MagicMock
from src.infrastructure.models import resolve_model
from src.utils.errors import ModelResolutionError


@patch("src.infrastructure.models.requests.get")
def test_resolve_ollama_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "llama3.1:latest"}]}
    mock_get.return_value = mock_resp

    llm = resolve_model("ollama", "llama3.1")
    assert llm.model == "llama3.1:latest"


@patch("src.infrastructure.models.requests.get")
def test_resolve_ollama_not_found(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"models": [{"name": "mistral"}]}
    mock_get.return_value = mock_resp

    with pytest.raises(ModelResolutionError, match="Unable to search"):
        resolve_model("ollama", "nonexistent")


def test_resolve_google_missing_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ModelResolutionError, match="GOOGLE_API_KEY not set"):
        resolve_model("google", "gemini-pro")
