"""Centralized JSON logging configuration."""

import logging
import json
import sys
from pathlib import Path
from src.infrastructure.config import settings


def setup_logging(log_dir: str = "logs", level: str = "INFO") -> None:
    """Configure structured JSON logging with file & console handlers."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "module": record.module,
                "message": record.getMessage(),
            }
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            standard_keys = {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "taskName",
            }
            for key, val in record.__dict__.items():
                if key not in standard_keys and key not in log_entry:
                    log_entry[key] = val

            # 🔐 Redact secrets if enabled
            if settings.REDACT_SECRETS_IN_LOGS:
                import re

                msg_str = json.dumps(log_entry)
                msg_str = re.sub(r"(sk-[A-Za-z0-9_\-]{20,})", "sk-***REDACTED***", msg_str)
                msg_str = re.sub(r"(oc_[A-Za-z0-9_\-]{20,})", "oc_***REDACTED***", msg_str)
                msg_str = re.sub(r"(AIza[A-Za-z0-9_\-]{20,})", "AIza***REDACTED***", msg_str)
                return msg_str
            return json.dumps(log_entry)

    logger = logging.getLogger("sandman")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(JSONFormatter())
    logger.addHandler(console)

    file_handler = logging.FileHandler(log_path / "sandman.jsonl")
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
