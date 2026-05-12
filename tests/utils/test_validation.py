import pytest
from pathlib import Path
from src.utils.validation import validate_package_name, sanitize_packages, safe_workspace_path


def test_validate_package_name():
    assert validate_package_name("requests") is True
    assert validate_package_name("numpy==1.24.0") is True
    assert validate_package_name("bad pkg") is False
    assert validate_package_name("rm -rf /") is False


def test_sanitize_packages():
    pkgs = ["requests", "  numpy ", "bad pkg", "", "pandas"]
    assert sanitize_packages(pkgs) == ["requests", "numpy", "pandas"]


def test_safe_workspace_path(tmp_workspace):
    valid = safe_workspace_path(tmp_workspace, "sess1", "main.py")
    assert valid == tmp_workspace / "sess1" / "main.py"


def test_safe_workspace_path_traversal(tmp_workspace):
    with pytest.raises(ValueError, match="traversal detected"):
        safe_workspace_path(tmp_workspace, "sess1", "../../etc/passwd")
