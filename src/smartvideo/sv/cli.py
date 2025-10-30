import os
import sys
import subprocess
import argparse
from pathlib import Path

def _pkg_root() -> Path:
    """
    Return the root directory of the package.

    Returns:
        Path: The path to the package root (../smartvideo).
    """
    return Path(__file__).resolve().parents[1]

def _effective_max_upload_mb(cli_value: int | None) -> int:
    """
    Determine the effective max upload size in megabytes.

    Priority:
    1. CLI argument (if provided)
    2. Environment variable STREAMLIT_SERVER_MAX_UPLOAD_SIZE
    3. Default value (2048 MB)

    Args:
        cli_value (int | None): Max upload size passed via CLI.

    Returns:
        int: The effective max upload size in MB.
    """
    if cli_value is not None:
        return cli_value

    env = os.getenv("STREAMLIT_SERVER_MAX_UPLOAD_SIZE")
    if env and env.isdigit():
        return int(env)

    return 2048

def run_ui():
    """
    Launch the SmartVideo Streamlit UI with configurable port and upload size.
    """
    parser = argparse.ArgumentParser(
        prog="svui",
        description="Run SmartVideo Streamlit UI"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8501"))
    )
    parser.add_argument(
        "--max-upload-mb",
        type=int,
        default=None,
        help=(
            "Override max upload size in MB "
            "(default 2048, or STREAMLIT_SERVER_MAX_UPLOAD_SIZE)."
        )
    )
    args = parser.parse_args()

    max_mb = _effective_max_upload_mb(args.max_upload_mb)
    os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = str(max_mb)

    app_path = _pkg_root() / "ui" / "app.py"
    print(f"[svui] maxUploadSize = {max_mb} MB")
    print(f"[svui] launching Streamlit on port {args.port} → {app_path}")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            str(args.port)
        ],
        check=False,
    )

def run_api():
    """
    Launch the SmartVideo FastAPI server using Uvicorn.
    """
    parser = argparse.ArgumentParser(
        prog="svapi",
        description="Run SmartVideo FastAPI server"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("API_PORT", "8000"))
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload for development."
    )
    args = parser.parse_args()

    print(f"[svapi] launching Uvicorn on port {args.port}")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "smartvideo.sv.api:app",
            "--port",
            str(args.port)
        ] + (["--reload"] if args.reload else []),
        check=False,
    )