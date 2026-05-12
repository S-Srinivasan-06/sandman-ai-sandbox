"""Output packaging: file copy, zip bundle, Dockerfile generation."""

import shutil
from pathlib import Path
from src.infrastructure.config import settings
from src.utils.validation import safe_workspace_path


def package_output(session_id: str, target_file: str) -> str:
    workspace = settings.WORKSPACE_BASE / session_id
    src = safe_workspace_path(settings.WORKSPACE_BASE, session_id, target_file)
    dst_dir = settings.OUTPUT_DIR
    dst_dir.mkdir(parents=True, exist_ok=True)

    if not src.exists():
        return f"Output file not found: {src}"

    dst_file = dst_dir / target_file
    shutil.copy2(src, dst_file)

    bundle_name = f"bundle_{session_id[:8]}"
    bundle_dir = dst_dir / bundle_name
    bundle_dir.mkdir(exist_ok=True)

    for item in workspace.iterdir():
        if item.is_file():
            shutil.copy2(item, bundle_dir / item.name)

    dockerfile = (
        f"FROM python:3.11-slim\nWORKDIR /app\nCOPY . .\n"
        f"RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi\n"
        f'CMD ["python", "{target_file}"]\n'
    )
    (bundle_dir / "Dockerfile").write_text(dockerfile)

    zip_path = dst_dir / f"{bundle_name}.zip"
    shutil.make_archive(str(dst_dir / bundle_name), "zip", bundle_dir)
    shutil.rmtree(bundle_dir)

    content = dst_file.read_text(encoding="utf-8")
    return f"✅ CODE SAVED TO: {dst_file}\n📦 PORTABLE BUNDLE: {zip_path}\n\nFINAL CODE:\n```python\n{content}\n```"
