# -*- coding: utf-8 -*-
"""
process.py - Video processing module for the SmartVideo library
---------------------------------------------------------------
- Depends on FFmpeg and FFprobe included inside smartvideo/bin/
- Supports override via environment variables:
    SMARTVIDEO_FFMPEG
    SMARTVIDEO_FFPROBE
- Available functions:
    - ensure_binaries()         ← Verifies presence of tools
    - probe_duration()          ← Calculates video duration
    - run_ffmpeg_extract_clip() ← Extracts video clip
    - copy_file()               ← Copies files
"""

from pathlib import Path
from importlib import resources
import subprocess
import shutil
import os
import sys


def _exe(name: str) -> str:
    """Return the correct executable name depending on the OS."""
    return f"{name}.exe" if sys.platform.startswith("win") else name


def _bin_path(filename: str) -> Path:
    """
    Return the full path of the binary inside the package.

    Example: smartvideo/bin/ffmpeg.exe
    """
    try:
        return resources.files("smartvideo").joinpath("bin").joinpath(filename)
    except Exception:
        # Fallback for development environments
        return Path(__file__).resolve().parents[3] / "bin" / filename


# Final binary paths (with environment variable support)
FFMPEG_PATH = os.getenv("SMARTVIDEO_FFMPEG", str(_bin_path(_exe("ffmpeg"))))
FFPROBE_PATH = os.getenv("SMARTVIDEO_FFPROBE", str(_bin_path(_exe("ffprobe"))))


def ensure_binaries():
    """
    Ensure that ffmpeg and ffprobe exist within the package or the system.

    Raises:
        FileNotFoundError: If required FFmpeg tools are missing.
    """
    missing = []
    for exe in [FFMPEG_PATH, FFPROBE_PATH]:
        if not Path(exe).exists():
            missing.append(exe)

    if missing:
        raise FileNotFoundError(
            "Required FFmpeg tools not found:\n"
            + "\n".join(f" - {m}" for m in missing)
            + "\nDownload FFmpeg from: https://www.gyan.dev/ffmpeg/builds/\n"
              "Or set paths using SMARTVIDEO_FFMPEG / SMARTVIDEO_FFPROBE."
        )


def probe_duration(src: Path) -> float | None:
    """
    Calculate the duration of a video in seconds using ffprobe.

    Args:
        src (Path): Path to the video file.

    Returns:
        float | None: Duration in seconds if successful; otherwise None.
    """
    ensure_binaries()
    try:
        result = subprocess.run(
            [
                FFMPEG_PATH.replace("ffmpeg", "ffprobe"),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(src)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        duration_str = result.stdout.strip()
        return float(duration_str) if duration_str else None
    except subprocess.CalledProcessError as e:
        print(f"[warn] ffprobe error: {e.stderr}")
        return None
    except Exception as e:
        print(f"[warn] Unexpected error in probe_duration: {e}")
        return None


def run_ffmpeg_extract_clip(src: Path, dst: Path, start: float, duration: float) -> None:
    """
    Extract a clip from a video using FFmpeg without re-encoding.

    Args:
        src (Path): Source video path.
        dst (Path): Destination path for the extracted clip.
        start (float): Start time in seconds.
        duration (float): Duration of the clip in seconds.

    Raises:
        subprocess.CalledProcessError: If FFmpeg command fails.
        Exception: For any unexpected errors.
    """
    ensure_binaries()
    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-ss", str(start),
        "-i", str(src),
        "-t", str(duration),
        "-c", "copy",
        str(dst)
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[ok] Clip extracted successfully: {dst}")
    except subprocess.CalledProcessError as e:
        print(f"[error] ffmpeg failed:\n{e.stderr.decode(errors='ignore') if hasattr(e.stderr, 'decode') else e}")
        raise
    except Exception as e:
        print(f"[error] Unexpected error in run_ffmpeg_extract_clip: {e}")
        raise


def copy_file(src: Path, dst: Path):
    """
    Copy a file to a specified destination, creating directories if needed.

    Args:
        src (Path): Source file path.
        dst (Path): Destination file path.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"[info] Copied: {src.name} → {dst}")