# -*- coding: utf-8 -*-
"""
process.py — Video processing utilities for SmartVideo
-----------------------------------------------------
- Relies on FFmpeg and FFprobe.
- Discovery order: ENV → system PATH → packaged binaries inside the wheel.
- Packaged paths: smartvideo/bin/ffmpeg(.exe), smartvideo/bin/ffprobe(.exe)

Environment overrides:
    SMARTVIDEO_FFMPEG
    SMARTVIDEO_FFPROBE

Public API:
    ensure_binaries() -> tuple[str, str]
    probe_duration(video: Path) -> float
    run_ffmpeg_extract_clip(src: Path, dst: Path, start: float|None, end: float|None, codec_copy: bool) -> None
    copy_file(src: Path, dst: Path) -> None
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from importlib import resources


# -----------------------------------------------------------------------------
# Binary discovery
# -----------------------------------------------------------------------------

def _pkg_bin(name: str) -> Path:
    """Return the absolute path to a packaged binary under smartvideo/bin/."""
    # resources.files available in Python 3.11+; shipped with Python 3.12 in your project
    return resources.files("smartvideo").joinpath("bin").joinpath(name)  # type: ignore[arg-type]


def _pick_names() -> Tuple[str, str]:
    """Executable names depending on OS."""
    if sys.platform.startswith("win"):
        return "ffmpeg.exe", "ffprobe.exe"
    return "ffmpeg", "ffprobe"


def _find_tool(name: str, env_var: str, packaged: Path) -> str:
    """
    Resolve a tool path by:
      1) explicit ENV var
      2) system PATH
      3) packaged fallback
    """
    # 1) Environment override
    env = os.getenv(env_var)
    if env:
        p = Path(env)
        if p.exists():
            return str(p)

    # 2) System PATH
    found = shutil.which(name)
    if found:
        return found

    # 3) Packaged fallback
    if packaged.exists():
        return str(packaged)

    raise FileNotFoundError(
        f"Required tool not found: {name}\n"
        f"Set {env_var}, install FFmpeg, or include it at: {packaged}"
    )


def ensure_binaries() -> Tuple[str, str]:
    """
    Ensure both ffmpeg and ffprobe are available and return their absolute paths.
    Resolution order: ENV → PATH → packaged wheel.
    """
    ffmpeg_name, ffprobe_name = _pick_names()
    ffmpeg_path = _find_tool(ffmpeg_name, "SMARTVIDEO_FFMPEG", _pkg_bin(ffmpeg_name))
    ffprobe_path = _find_tool(ffprobe_name, "SMARTVIDEO_FFPROBE", _pkg_bin(ffprobe_name))
    return ffmpeg_path, ffprobe_path


# Optionally expose globals for convenience (lazy-resolved at import)
try:
    FFMPEG_PATH, FFPROBE_PATH = ensure_binaries()
except Exception:
    # Don't crash at import-time; endpoints will call ensure_binaries() anyway.
    FFMPEG_PATH = os.getenv("SMARTVIDEO_FFMPEG", "")
    FFPROBE_PATH = os.getenv("SMARTVIDEO_FFPROBE", "")


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess and raise a helpful error if it fails."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(cmd)
            + "\n--- STDOUT ---\n"
            + proc.stdout
            + "\n--- STDERR ---\n"
            + proc.stderr
        )
    return proc


# -----------------------------------------------------------------------------
# Probing & processing
# -----------------------------------------------------------------------------

def probe_duration(video: Path) -> float:
    """
    Return the duration (in seconds) of a video file using ffprobe.
    """
    if not Path(video).exists():
        raise FileNotFoundError(f"Video not found: {video}")

    _, ffprobe = ensure_binaries()

    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    proc = _run(cmd)

    try:
        sec = float(proc.stdout.strip())
    except ValueError as e:
        raise RuntimeError(f"Unable to parse duration for {video!s}") from e

    return sec


def run_ffmpeg_extract_clip(
    src: Path,
    dst: Path,
    start: Optional[float] = None,
    end: Optional[float] = None,
    codec_copy: bool = True,
) -> None:
    """
    Extract a clip from `src` and save to `dst`.

    Args:
        src: Source video path.
        dst: Output video path (created/overwritten).
        start: start time in seconds (optional).
        end: end time in seconds (optional). If provided with start, uses -to; if only end, uses -t=end.
        codec_copy: if True, use stream copy (-c copy); otherwise transcode to H.264/AAC.

    Notes:
        - If only `start` is provided → from start to end-of-file.
        - If `start` and `end` provided → clip between them.
        - If only `end` provided → first `end` seconds from the beginning.
    """
    if not Path(src).exists():
        raise FileNotFoundError(f"Source video not found: {src}")

    ffmpeg, _ = ensure_binaries()

    # Build ffmpeg args
    args: list[str] = [ffmpeg, "-y"]

    # Time arguments
    if start is not None and start >= 0:
        # Place -ss before -i for faster seeking
        args += ["-ss", f"{start}"]

    args += ["-i", str(src)]

    if start is not None and end is not None and end >= start:
        # Use -to with absolute end-time relative to input start
        args += ["-to", f"{end}"]
    elif start is None and end is not None and end >= 0:
        # Extract first `end` seconds
        args += ["-t", f"{end}"]

    # Codec settings
    if codec_copy:
        args += ["-c", "copy"]
    else:
        # Reasonable defaults for wide compatibility
        args += [
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
        ]

    # Ensure destination directory exists
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    args.append(str(dst))

    _run(args)


# -----------------------------------------------------------------------------
# File utilities
# -----------------------------------------------------------------------------

def copy_file(src: Path, dst: Path) -> None:
    """
    Copy a file to destination, creating directories if needed.
    """
    if not Path(src).exists():
        raise FileNotFoundError(f"Source file not found: {src}")
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
