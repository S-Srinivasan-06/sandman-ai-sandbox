import pytest
from src.infrastructure.config import Settings, LANGUAGE_CONFIG


def test_settings_defaults():
    s = Settings()
    assert s.MAX_RETRIES == 3
    assert s.EXEC_TIMEOUT == 600
    assert s.SANDBOX_USER == "1000:1000"


def test_language_config_structure():
    for lang in ["python", "node", "go"]:
        assert lang in LANGUAGE_CONFIG
        cfg = LANGUAGE_CONFIG[lang]
        assert "image" in cfg
        assert "run_cmd" in cfg
        assert "pkg_manager" in cfg
