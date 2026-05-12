import pytest
from pathlib import Path
import zipfile
from src.core.output import package_output


def test_package_output_success(tmp_workspace, tmp_outputs, monkeypatch):
    monkeypatch.setattr("src.core.output.settings.WORKSPACE_BASE", tmp_workspace)
    monkeypatch.setattr("src.core.output.settings.OUTPUT_DIR", tmp_outputs)

    sess = tmp_workspace / "sess1"
    sess.mkdir()
    (sess / "main.py").write_text("print('hi')")

    result = package_output("sess1", "main.py")
    assert "CODE SAVED TO" in result
    assert (tmp_outputs / "main.py").exists()

    # Verify zip bundle
    zips = list(tmp_outputs.glob("bundle_*.zip"))
    assert len(zips) == 1
    with zipfile.ZipFile(zips[0]) as zf:
        assert "main.py" in zf.namelist()
        assert "Dockerfile" in zf.namelist()


def test_package_output_missing_file(tmp_workspace, tmp_outputs, monkeypatch):
    monkeypatch.setattr("src.core.output.settings.WORKSPACE_BASE", tmp_workspace)
    monkeypatch.setattr("src.core.output.settings.OUTPUT_DIR", tmp_outputs)

    result = package_output("sess_missing", "main.py")
    assert "not found" in result
