"""Centralized configuration & permissions manager."""

import os
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    # 🔐 SANDBOX PERMISSIONS & SECURITY
    ALLOW_NETWORK_DEFAULT: bool = Field(
        default=False, description="Default network access for new sandboxes"
    )
    ALLOW_DEPENDENCY_INSTALL: bool = Field(
        default=True, description="Allow pip/apt/npm installs inside sandbox"
    )
    ALLOW_ROOT_DEP_INSTALL: bool = Field(
        default=True, description="Allow root privileges for dependency installation"
    )
    CONTAINER_AUTO_REMOVE: bool = Field(default=False, description="Auto-remove container on stop")
    CONTAINER_READ_ONLY_ROOT: bool = Field(
        default=True, description="Mount root filesystem as read-only"
    )
    CONTAINER_CAP_DROP: List[str] = Field(default=["ALL"], description="Linux capabilities to drop")
    CONTAINER_SECURITY_OPT: List[str] = Field(
        default=["no-new-privileges"], description="Docker security options"
    )
    DISABLE_IPV6: bool = Field(
        default=True, description="Disable IPv6 inside containers to prevent DNS hangs"
    )
    CONTAINER_DNS: List[str] = Field(
        default=["8.8.8.8", "1.1.1.1"], description="DNS servers for network-enabled sandboxes"
    )
    SANDBOX_USER: str = Field(
        default="1000:1000", description="Non-root user UID:GID for code execution"
    )
    ALLOWED_IMAGES: dict = Field(
        default={"python": "python:3.11-slim", "node": "node:20-slim", "go": "golang:1.22-alpine"}
    )

    # ⚡ RESOURCE & EXECUTION LIMITS
    MEM_LIMIT: str = Field(default="512m", description="Container memory limit")
    CPU_QUOTA: int = Field(
        default=50000, ge=10000, le=200000, description="CPU quota in microseconds"
    )
    TMPFS_SIZE: str = Field(default="500m", description="Size of /tmp tmpfs mount")
    EXEC_TIMEOUT: int = Field(
        default=1200, ge=10, le=7200, description="Max seconds for script execution"
    )
    DEP_INSTALL_TIMEOUT: int = Field(
        default=1200, ge=30, le=3600, description="Max seconds for dependency installation"
    )
    MAX_RETRIES: int = Field(default=3, ge=1, le=10, description="Max self-healing retry attempts")

    # 🤖 AGENT & CONTEXT LIMITS
    MAX_CHAT_HISTORY: int = Field(
        default=8, ge=2, le=50, description="Max messages to retain in context window"
    )
    ENABLE_OLLAMA_VRAM_CLEANUP: bool = Field(
        default=True, description="Unload Ollama model after session to free VRAM"
    )

    # 📂 PATHS & LOGGING
    WORKSPACE_BASE: Path = Field(default=Path("sandbox_workspace"))
    OUTPUT_DIR: Path = Field(default=Path("outputs"))
    LOG_DIR: Path = Field(default=Path("logs"))
    LOG_LEVEL: str = Field(default="INFO")
    REDACT_SECRETS_IN_LOGS: bool = Field(
        default=True, description="Strip API keys/secrets from log output"
    )

    # 🔑 PROVIDER CREDENTIALS
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OPENAI_BASE_URL: str | None = None
    GOOGLE_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    BYOK_API_KEY: str | None = None
    BYOK_BASE_URL: str | None = None
    OLLAMA_CLOUD_API_KEY: str | None = None
    OLLAMA_CLOUD_BASE_URL: str = Field(default="https://api.ollama.com/v1")
    SESSION_TIME_BUDGET_MINUTES: int = Field(
        default=30, ge=5, le=240, description="Auto-destroy sandbox after X minutes"
    )
    ALLOWED_CUSTOM_IMAGES: list[str] = Field(
        default=[], description="Allowlist for custom Docker images"
    )
    ENABLE_PERSISTENT_SANDBOXES: bool = Field(default=True)
    MAX_ACTIVE_SESSIONS: int = Field(default=5, ge=1, le=20)

    @field_validator("WORKSPACE_BASE", "OUTPUT_DIR", "LOG_DIR", mode="before")
    @classmethod
    def resolve_paths(cls, v: str | Path) -> Path:
        return Path(v).resolve()

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()

LANGUAGE_CONFIG = {
    "python": {
        "image": "python:3.11-slim",
        "run_cmd": "python {file}",
        "test_cmd": "python -m pytest {test_file} -v",
        "pkg_manager": "pip",
    },
    "node": {
        "image": "node:20-slim",
        "run_cmd": "node {file}",
        "test_cmd": "npx jest {test_file} --verbose",
        "pkg_manager": "npm",
    },
    "go": {
        "image": "golang:1.22-alpine",
        "run_cmd": "go run {file}",
        "test_cmd": "go test -v ./...",
        "pkg_manager": "go",
    },
}
