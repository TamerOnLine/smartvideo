# -*- coding: utf-8 -*-
"""
process.py — SmartVideo runtime FFmpeg resolver & helpers
- Discovery order: ENV -> PATH -> packaged (if exists) -> auto-download to data dir
- Data dir (Windows): %LOCALAPPDATA%/SmartVideo/bin

Environment overrides:
    SMARTVIDEO_FFMPEG
    SMARTVIDEO_FFPROBE
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
import zipfile
import logging
from pathlib import Path
from typing import Tuple, Optional
from importlib import resources

import requests
from platformdirs import PlatformDirs

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logger = logging.getLogger("smartvideo")
if not logger.handlers:
    # لا تكرر الإضافة إذا كان المستهلك قد ضبط اللوغر من قبل
    _h = logging.StreamHandler()
    _fmt = logging.Formatter("[%(levelname)s] smartvideo: %(message)s")
    _h.setFormatter(_fmt)
    logger.addHandler(_h)
    # اجعل المستوى INFO افتراضيًا (يمكن للتطبيق تغييره لاحقًا)
    logger.setLevel(logging.INFO)

APP_NAME = "SmartVideo"
APP_AUTHOR = "TamerOnLine"

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
def _data_bin_dir() -> Path:
    d = PlatformDirs(APP_NAME, APP_AUTHOR)
    p = Path(d.user_data_dir) / "bin"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _pkg_bin(name: str) -> Path:
    # ملاحظة: غالبًا لن تُشحن داخل العجلة لتجنب الحجم؛ لا مشكلة لو كان المجلد فارغًا
    return resources.files("smartvideo").joinpath("bin").joinpath(name)  # type: ignore[arg-type]


def _exe_names() -> Tuple[str, str]:
    if sys.platform.startswith("win"):
        return "ffmpeg.exe", "ffprobe.exe"
    return "ffmpeg", "ffprobe"

# -----------------------------------------------------------------------------
# Downloads (Windows)
# -----------------------------------------------------------------------------
def _win_ffmpeg_zip_url() -> str:
    # Windows static build (essentials)
    return "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-release-essentials.zip"


def _download(url: str, dest: Path, timeout: int = 60) -> None:
    logger.info(f"Downloading FFmpeg bundle from: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", "0") or 0)
        read = 0
        chunk = 1 << 20  # 1 MB
        with open(dest, "wb") as f:
            for part in r.iter_content(chunk_size=chunk):
                if not part:
                    continue
                f.write(part)
                read += len(part)
                if total:
                    pct = (read / total) * 100
                    logger.info(f"  ... {read/1e6:.1f} MB / {total/1e6:.1f} MB ({pct:.0f}%)")
    logger.info(f"Saved: {dest} ({dest.stat().st_size/1e6:.1f} MB)")


def _ensure_win_binaries_to(dir_bin: Path) -> Tuple[Path, Path]:
    """
    Download a Windows FFmpeg zip, extract ffmpeg.exe & ffprobe.exe into dir_bin.
    Returns paths to the two executables.
    """
    zip_path = dir_bin / "ffmpeg.zip"
    _download(_win_ffmpeg_zip_url(), zip_path)

    logger.info("Extracting FFmpeg...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        ffmpeg_member = next((m for m in zf.namelist() if m.endswith("/bin/ffmpeg.exe")), None)
        ffprobe_member = next((m for m in zf.namelist() if m.endswith("/bin/ffprobe.exe")), None)
        if not ffmpeg_member or not ffprobe_member:
            raise RuntimeError("ffmpeg.zip does not contain expected binaries (ffmpeg.exe/ffprobe.exe).")

        zf.extract(ffmpeg_member, dir_bin)
        zf.extract(ffprobe_member, dir_bin)
        src_ffmpeg = dir_bin / ffmpeg_member
        src_ffprobe = dir_bin / ffprobe_member

    final_ffmpeg = dir_bin / "ffmpeg.exe"
    final_ffprobe = dir_bin / "ffprobe.exe"

    final_ffmpeg.write_bytes(src_ffmpeg.read_bytes())
    final_ffprobe.write_bytes(src_ffprobe.read_bytes())

    # تنظيف الشجرة المفكوكة والملف المضغوط
    try:
        shutil.rmtree(dir_bin / ffmpeg_member.split("/")[0], ignore_errors=True)
        zip_path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception as e:
        logger.debug(f"Cleanup warning: {e}")

    logger.info(f"FFmpeg ready: {final_ffmpeg}")
    logger.info(f"FFprobe ready: {final_ffprobe}")
    return final_ffmpeg, final_ffprobe


def _auto_download(dir_bin: Path) -> Tuple[Path, Path]:
    """
    Download platform-specific binaries into dir_bin and return their paths.
    """
    if sys.platform.startswith("win"):
        return _ensure_win_binaries_to(dir_bin)

    raise FileNotFoundError(
        "FFmpeg not found and auto-download is only implemented for Windows currently. "
        "Please install FFmpeg via your package manager or set SMARTVIDEO_FFMPEG / SMARTVIDEO_FFPROBE."
    )

# -----------------------------------------------------------------------------
# Resolver
# -----------------------------------------------------------------------------
def _find_tool(name: str, env_var: str, packaged: Path, data_bin: Path) -> str:
    # 1) ENV override
    env = os.getenv(env_var)
    if env and Path(env).exists():
        logger.info(f"Using {name} from ENV: {env_var}={env}")
        return env

    # 2) PATH
    found = shutil.which(name)
    if found:
        logger.info(f"Using {name} from PATH: {found}")
        return found

    # 3) Packaged (if present)
    if packaged.exists():
        logger.info(f"Using packaged {name}: {packaged}")
        return str(packaged)

    # 4) Cached in data dir?
    candidate = data_bin / name
    if candidate.exists():
        logger.info(f"Using cached {name} in data dir: {candidate}")
        return str(candidate)

    # 5) Auto-download (Windows)
    logger.info(f"{name} not found (ENV/PATH/packaged/cache). Auto-downloading...")
    if sys.platform.startswith("win"):
        ffmpeg_p, ffprobe_p = _auto_download(data_bin)
        chosen = ffmpeg_p if name.startswith("ffmpeg") else ffprobe_p
        logger.info(f"Using downloaded {name}: {chosen}")
        return str(chosen)

    raise FileNotFoundError(
        f"{name} not found. Install FFmpeg or set {env_var} to the executable path."
    )


def ensure_binaries() -> Tuple[str, str]:
    """
    Ensure ffmpeg & ffprobe exist (ENV -> PATH -> packaged -> auto-download to data dir).
    Returns absolute string paths.
    """
    data_bin = _data_bin_dir()
    ffmpeg_n, ffprobe_n = _exe_names()
    ffmpeg = _find_tool(ffmpeg_n, "SMARTVIDEO_FFMPEG", _pkg_bin(ffmpeg_n), data_bin)
    ffprobe = _find_tool(ffprobe_n, "SMARTVIDEO_FFPROBE", _pkg_bin(ffprobe_n), data_bin)
    return ffmpeg, ffprobe

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    logger.info("Running: " + " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        logger.error("--- STDOUT ---\n" + proc.stdout)
        logger.error("--- STDERR ---\n" + proc.stderr)
        raise RuntimeError("Command failed (see logs above).")
    return proc

# -----------------------------------------------------------------------------
# Public operations
# -----------------------------------------------------------------------------
def probe_duration(video: Path) -> float:
    if not Path(video).exists():
        raise FileNotFoundError(f"Video not found: {video}")
    _, ffprobe = ensure_binaries()
    proc = _run([
        ffprobe, "-v", "error", "-select_streams", "v:0",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video),
    ])
    try:
        return float(proc.stdout.strip())
    except ValueError as e:
        raise RuntimeError(f"Unable to parse duration for {video!s}") from e


def run_ffmpeg_extract_clip(
    src: Path,
    dst: Path,
    start: Optional[float] = None,
    end: Optional[float] = None,
    codec_copy: bool = True,
) -> None:
    if not Path(src).exists():
        raise FileNotFoundError(f"Source video not found: {src}")

    ffmpeg, _ = ensure_binaries()
    args: list[str] = [ffmpeg, "-y"]

    if start is not None and start >= 0:
        args += ["-ss", f"{start}"]

    args += ["-i", str(src)]

    if start is not None and end is not None and end >= start:
        args += ["-to", f"{end}"]
    elif start is None and end is not None and end >= 0:
        args += ["-t", f"{end}"]

    if codec_copy:
        args += ["-c", "copy"]
    else:
        args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                 "-c:a", "aac", "-b:a", "128k"]

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    args.append(str(dst))

    _run(args)
