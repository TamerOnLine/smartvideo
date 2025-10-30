from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "SmartVideo"

def get_data_dirs() -> tuple[Path, Path]:
    """
    Return the paths for the 'uploads' and 'outputs' directories.

    Priority:
    1. Environment variable SMARTVIDEO_DATA_DIR (if set)
    2. './data' in the current working directory

    Returns:
        tuple[Path, Path]: A tuple containing paths to the uploads and outputs directories.
    """
    base = Path(os.getenv("SMARTVIDEO_DATA_DIR", Path.cwd() / "data")).resolve()

    uploads = base / "uploads"
    outputs = base / "outputs"

    uploads.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)

    return uploads, outputs


# Initialize upload/output directories once when this file is imported
UPLOADS_DIR, OUTPUTS_DIR = get_data_dirs()

# Optional debug printing of paths if SMARTVIDEO_DEBUG is set
if os.getenv("SMARTVIDEO_DEBUG"):
    print(f"[{APP_NAME}] Uploads: {UPLOADS_DIR}")
    print(f"[{APP_NAME}] Outputs: {OUTPUTS_DIR}")
