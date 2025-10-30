# -*- coding: utf-8 -*-
"""
process.py — SmartVideo runtime FFmpeg resolver & helpers
----------------------------------------------------------
- Discovery order: ENV → PATH → packaged (if exists) → cached → auto-download
- Data dir:
    - Windows:  %LOCALAPPDATA%/SmartVideo/bin
    - Linux/Mac: ~/.local/share/SmartVideo/bin  (حسب platformdirs)

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
import tarfile
import logging
import platform
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
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] smartvideo: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

APP_NAME = "SmartVideo"
APP_AUTHOR = "TamerOnLine"


# -----------------------------------------------------------------------------
# Helper paths
# -----------------------------------------------------------------------------
def _data_bin_dir() -> Path:
    """Return user data bin dir (e.g., AppData/SmartVideo/bin)."""
    d = PlatformDirs(APP_NAME, APP_AUTHOR)
    p = Path(d.user_data_dir) / "bin"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _pkg_bin(name: str) -> Path:
    """Return packaged binary (if shipped inside the wheel)."""
    return resources.files("smartvideo").joinpath("bin").joinpath(name)  # type: ignore[arg-type]


def _exe_names() -> Tuple[str, str]:
    """Return executable names depending on OS."""
    if sys.platform.startswith("win"):
        return "ffmpeg.exe", "ffprobe.exe"
    return "ffmpeg", "ffprobe"


def _chmod_x(p: Path) -> None:
    try:
        mode = p.stat().st_mode
        p.chmod(mode | 0o755)
    except Exception as e:
        logger.warning(f"Failed to chmod +x on {p}: {e}")


# -----------------------------------------------------------------------------
# Generic download helper
# -----------------------------------------------------------------------------
def _download_first_ok(urls: list[str], dest: Path, timeout: int = 120) -> str:
    """Try downloading from multiple mirrors until success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    last_err = None
    for url in urls:
        logger.info(f"Downloading FFmpeg bundle from: {url}")
        try:
            with requests.get(url, stream=True, timeout=timeout, headers={"User-Agent": "smartvideo/1.0"}) as r:
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
            return url
        except Exception as e:
            last_err = e
            logger.warning(f"Failed to download from {url}: {e}")
            try:
                if dest.exists():
                    dest.unlink()
            except Exception:
                pass
    raise RuntimeError(f"Failed to download FFmpeg from all mirrors: {urls}\nLast error: {last_err}")


# -----------------------------------------------------------------------------
# Windows auto-download
# -----------------------------------------------------------------------------
def _win_ffmpeg_zip_urls() -> list[str]:
    """Mirrors for Windows FFmpeg builds."""
    return [
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
        "https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.zip",
    ]


def _ensure_win_binaries_to(dir_bin: Path) -> Tuple[Path, Path]:
    """Download and extract ffmpeg.exe + ffprobe.exe to dir_bin."""
    zip_path = dir_bin / "ffmpeg.zip"
    _download_first_ok(_win_ffmpeg_zip_urls(), zip_path)

    logger.info("Extracting FFmpeg (Windows)...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        ffmpeg_member = next((m for m in zf.namelist() if m.endswith("/bin/ffmpeg.exe")), None)
        ffprobe_member = next((m for m in zf.namelist() if m.endswith("/bin/ffprobe.exe")), None)
        if not ffmpeg_member or not ffprobe_member:
            raise RuntimeError("ffmpeg.zip does not contain expected binaries.")

        zf.extract(ffmpeg_member, dir_bin)
        zf.extract(ffprobe_member, dir_bin)

        src_ffmpeg = dir_bin / ffmpeg_member
        src_ffprobe = dir_bin / ffprobe_member

    final_ffmpeg = dir_bin / "ffmpeg.exe"
    final_ffprobe = dir_bin / "ffprobe.exe"

    final_ffmpeg.write_bytes(src_ffmpeg.read_bytes())
    final_ffprobe.write_bytes(src_ffprobe.read_bytes())

    # Cleanup
    try:
        shutil.rmtree(dir_bin / ffmpeg_member.split("/")[0], ignore_errors=True)
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        logger.debug(f"Cleanup warning: {e}")

    logger.info(f"FFmpeg ready: {final_ffmpeg}")
    logger.info(f"FFprobe ready: {final_ffprobe}")
    return final_ffmpeg, final_ffprobe


# -----------------------------------------------------------------------------
# Linux auto-download (static builds)
# -----------------------------------------------------------------------------
def _linux_static_urls() -> dict:
    """
    Return URLs for Linux static builds by arch.
    Using John Van Sickle static builds (widely used).
    """
    return {
        "x86_64": [
            "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        ],
        "aarch64": [
            "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
        ],
        # Fallback aliases
        "amd64": [
            "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
        ],
        "arm64": [
            "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
        ],
    }


def _ensure_linux_binaries_to(dir_bin: Path) -> Tuple[Path, Path]:
    arch = platform.machine().lower()
    urls_map = _linux_static_urls()
    urls = urls_map.get(arch) or urls_map.get("x86_64")
    if not urls:
        raise RuntimeError(f"Unsupported Linux arch for auto-download: {arch}")

    tar_path = dir_bin / "ffmpeg-linux.tar.xz"
    _download_first_ok(urls, tar_path)

    logger.info("Extracting FFmpeg (Linux)...")
    with tarfile.open(tar_path, "r:xz") as tf:
        members = tf.getmembers()
        ffmpeg_member = next((m for m in members if m.name.endswith("/ffmpeg")), None)
        ffprobe_member = next((m for m in members if m.name.endswith("/ffprobe")), None)
        if not ffmpeg_member or not ffprobe_member:
            raise RuntimeError("Archive does not contain ffmpeg/ffprobe.")
        tf.extract(ffmpeg_member, dir_bin)
        tf.extract(ffprobe_member, dir_bin)

        src_ffmpeg = (dir_bin / ffmpeg_member.name).resolve()
        src_ffprobe = (dir_bin / ffprobe_member.name).resolve()

    final_ffmpeg = dir_bin / "ffmpeg"
    final_ffprobe = dir_bin / "ffprobe"

    shutil.copy2(src_ffmpeg, final_ffmpeg)
    shutil.copy2(src_ffprobe, final_ffprobe)
    _chmod_x(final_ffmpeg)
    _chmod_x(final_ffprobe)

    # Cleanup
    try:
        # remove extracted directory root if present
        root = ffmpeg_member.name.split("/")[0]
        shutil.rmtree(dir_bin / root, ignore_errors=True)
        tar_path.unlink(missing_ok=True)
    except Exception as e:
        logger.debug(f"Cleanup warning: {e}")

    logger.info(f"FFmpeg ready: {final_ffmpeg}")
    logger.info(f"FFprobe ready: {final_ffprobe}")
    return final_ffmpeg, final_ffprobe


# -----------------------------------------------------------------------------
# macOS auto-download (universal fallback)
# -----------------------------------------------------------------------------
def _mac_urls() -> dict:
    """
    Return URLs for macOS prebuilt binaries.
    We try common mirrors; order matters. You can adjust to your preferred source.
    """
    return {
        "arm64": {
            "ffmpeg": [
                # BtbN macOS arm64 builds (GPL). Adjust if needed.
                "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-macos64-arm64-gpl.zip",
            ],
            "ffprobe": [
                "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffprobe-master-latest-macos64-arm64-gpl.zip",
            ],
        },
        "x86_64": {
            "ffmpeg": [
                "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-macos64-gpl.zip",
            ],
            "ffprobe": [
                "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffprobe-master-latest-macos64-gpl.zip",
            ],
        },
        # Fallback aliases
        "universal": {
            "ffmpeg": [
                "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-macos64-gpl.zip",
            ],
            "ffprobe": [
                "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffprobe-master-latest-macos64-gpl.zip",
            ],
        },
    }


def _ensure_macos_binaries_to(dir_bin: Path) -> Tuple[Path, Path]:
    arch = platform.machine().lower()
    table = _mac_urls()
    arch_key = arch if arch in table else "universal"
    urls_ffmpeg = table[arch_key]["ffmpeg"]
    urls_ffprobe = table[arch_key]["ffprobe"]

    ff_zip = dir_bin / "ffmpeg-mac.zip"
    fp_zip = dir_bin / "ffprobe-mac.zip"

    _download_first_ok(urls_ffmpeg, ff_zip)
    _download_first_ok(urls_ffprobe, fp_zip)

    logger.info("Extracting FFmpeg (macOS)...")
    with zipfile.ZipFile(ff_zip, "r") as zf:
        # Try common names
        cand = [m for m in zf.namelist() if m.endswith("/bin/ffmpeg") or m.endswith("ffmpeg")]
        if not cand:
            raise RuntimeError("ffmpeg zip: ffmpeg not found.")
        zf.extract(cand[0], dir_bin)
        src_ffmpeg = (dir_bin / cand[0]).resolve()

    with zipfile.ZipFile(fp_zip, "r") as zf:
        cand = [m for m in zf.namelist() if m.endswith("/bin/ffprobe") or m.endswith("ffprobe")]
        if not cand:
            raise RuntimeError("ffprobe zip: ffprobe not found.")
        zf.extract(cand[0], dir_bin)
        src_ffprobe = (dir_bin / cand[0]).resolve()

    final_ffmpeg = dir_bin / "ffmpeg"
    final_ffprobe = dir_bin / "ffprobe"

    shutil.copy2(src_ffmpeg, final_ffmpeg)
    shutil.copy2(src_ffprobe, final_ffprobe)
    _chmod_x(final_ffmpeg)
    _chmod_x(final_ffprobe)

    # Cleanup
    try:
        # Try to remove extracted root directories if any
        for p in (src_ffmpeg, src_ffprobe):
            try:
                root = [part for part in p.parts if part.lower().startswith("ffmpeg") or part.lower().startswith("ffprobe")]
                if root:
                    shutil.rmtree(dir_bin / root[0], ignore_errors=True)
            except Exception:
                pass
        ff_zip.unlink(missing_ok=True)
        fp_zip.unlink(missing_ok=True)
    except Exception as e:
        logger.debug(f"Cleanup warning: {e}")

    logger.info(f"FFmpeg ready: {final_ffmpeg}")
    logger.info(f"FFprobe ready: {final_ffprobe}")
    return final_ffmpeg, final_ffprobe


# -----------------------------------------------------------------------------
# Platform auto-download dispatcher
# -----------------------------------------------------------------------------
def _auto_download(dir_bin: Path) -> Tuple[Path, Path]:
    """Platform-specific download fallback."""
    if sys.platform.startswith("win"):
        return _ensure_win_binaries_to(dir_bin)
    if sys.platform.startswith("linux"):
        return _ensure_linux_binaries_to(dir_bin)
    if sys.platform.startswith("darwin"):
        return _ensure_macos_binaries_to(dir_bin)

    raise FileNotFoundError(
        "FFmpeg not found and no auto-download available for this OS.\n"
        "Please install FFmpeg manually or set SMARTVIDEO_FFMPEG / SMARTVIDEO_FFPROBE."
    )


# -----------------------------------------------------------------------------
# Binary resolver (ENV → PATH → packaged → cached → auto-download)
# -----------------------------------------------------------------------------
def _find_tool(name: str, env_var: str, packaged: Path, data_bin: Path) -> str:
    """Resolve binary from ENV → PATH → packaged → cached → auto-download."""
    env = os.getenv(env_var)
    if env and Path(env).exists():
        logger.info(f"Using {name} from ENV: {env}")
        return env

    found = shutil.which(name)
    if found:
        logger.info(f"Using {name} from PATH: {found}")
        return found

    if packaged.exists():
        logger.info(f"Using packaged {name}: {packaged}")
        return str(packaged)

    cached = data_bin / name
    if cached.exists():
        logger.info(f"Using cached {name}: {cached}")
        return str(cached)

    logger.info(f"{name} not found (ENV/PATH/packaged/cache). Auto-downloading...")
    ffmpeg_p, ffprobe_p = _auto_download(data_bin)
    chosen = ffmpeg_p if name.startswith("ffmpeg") else ffprobe_p
    logger.info(f"Using downloaded {name}: {chosen}")
    return str(chosen)


def ensure_binaries() -> Tuple[str, str]:
    """Ensure ffmpeg & ffprobe exist (ENV → PATH → packaged → auto-download)."""
    data_bin = _data_bin_dir()
    ffmpeg_n, ffprobe_n = _exe_names()
    ffmpeg = _find_tool(ffmpeg_n, "SMARTVIDEO_FFMPEG", _pkg_bin(ffmpeg_n), data_bin)
    ffprobe = _find_tool(ffprobe_n, "SMARTVIDEO_FFPROBE", _pkg_bin(ffprobe_n), data_bin)
    return ffmpeg, ffprobe


# -----------------------------------------------------------------------------
# Helper to run commands
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
    """Return video duration in seconds."""
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
    """Extract a clip from `src` and save to `dst`."""
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
