import json
import logging
from pathlib import Path
from src.utils.logging import setup_logging


def test_setup_logging_creates_handlers(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logging(str(log_dir), "INFO")
    logger = logging.getLogger("sandman")
    assert len(logger.handlers) == 2
    assert log_dir.exists()
    assert (log_dir / "sandman.jsonl").exists()


def test_json_formatter(tmp_path):
    log_dir = tmp_path / "logs"
    setup_logging(str(log_dir), "DEBUG")
    logger = logging.getLogger("sandman")
    logger.info("test_event", extra={"sandbox_id": "abc123"})

    log_file = log_dir / "sandman.jsonl"
    entry = json.loads(log_file.read_text().strip())
    assert entry["message"] == "test_event"
    assert entry["sandbox_id"] == "abc123"
    assert entry["level"] == "INFO"
