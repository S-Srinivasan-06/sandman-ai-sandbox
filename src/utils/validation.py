"""Input validation & sanitization helpers."""

import re
from pathlib import Path


def validate_package_name(name: str) -> bool:
    """Ensure package name is safe for pip/apt."""
    return bool(re.match(r"^[a-zA-Z0-9_\-\.\=<>]+$", name.strip()))


def sanitize_packages(packages: list[str]) -> list[str]:
    """Filter & validate package names."""
    return [p.strip() for p in packages if p.strip() and validate_package_name(p)]


def safe_workspace_path(base: Path, session_id: str, filename: str) -> Path:
    """Prevent path traversal attacks."""
    target = (base / session_id / filename).resolve()
    if not str(target).startswith(str(base.resolve())):
        raise ValueError("Invalid path: traversal detected")
    return target
