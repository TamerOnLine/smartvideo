# -*- coding: utf-8 -*-
"""
process.py — وحدة معالجة الفيديوهات لمشروع Smart Video
-------------------------------------------------------
• تعتمد على FFmpeg و FFprobe الموجودين في مجلد bin/
• تقوم بعمليات:
    - قراءة مدة الفيديو (probe_duration)
    - استخراج مقاطع من الفيديو (run_ffmpeg_extract_clip)
"""

from pathlib import Path
import subprocess
import shutil


# ---------------------------------------------------------
# 🔧 تحديد مسار الأدوات (ffmpeg و ffprobe)
# ---------------------------------------------------------
# هذا الملف موجود في: src/sv/core/services/process.py
# نرجع 4 مستويات للوصول إلى جذر المشروع: smart-video/
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# نحاول أولاً bin/ في الجذر
BIN_DIR = PROJECT_ROOT / "bin"
FFMPEG_PATH = str(BIN_DIR / "ffmpeg.exe")
FFPROBE_PATH = str(BIN_DIR / "ffprobe.exe")

# (اختياري) لو لم تكن الأدوات في الجذر، جرّب src/bin
if not Path(FFMPEG_PATH).exists() or not Path(FFPROBE_PATH).exists():
    ALT_BIN = PROJECT_ROOT / "src" / "bin"
    if ALT_BIN.exists():
        BIN_DIR = ALT_BIN
        FFMPEG_PATH = str(BIN_DIR / "ffmpeg.exe")
        FFPROBE_PATH = str(BIN_DIR / "ffprobe.exe")


# ---------------------------------------------------------
# ⚙️ التحقق من وجود الأدوات
# ---------------------------------------------------------
def ensure_binaries():
    """يتأكد من وجود ffmpeg و ffprobe داخل bin/."""
    missing = []
    if not Path(FFMPEG_PATH).exists():
        missing.append("ffmpeg.exe")
    if not Path(FFPROBE_PATH).exists():
        missing.append("ffprobe.exe")

    if missing:
        raise FileNotFoundError(
            f"❌ لم يتم العثور على الملفات التالية داخل {BIN_DIR}:\n"
            + "\n".join(f" - {m}" for m in missing)
            + "\nيرجى تنزيل FFmpeg من: https://www.gyan.dev/ffmpeg/builds/"
        )


# ---------------------------------------------------------
# 🧭 قراءة مدة الفيديو
# ---------------------------------------------------------
def probe_duration(src: Path) -> float | None:
    """
    يحسب مدة الفيديو بالثواني باستخدام ffprobe.
    """
    ensure_binaries()
    try:
        result = subprocess.run(
            [
                FFPROBE_PATH,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(src)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        duration_str = result.stdout.strip()
        return float(duration_str) if duration_str else None

    except subprocess.CalledProcessError as e:
        print(f"[warn] ffprobe error: {e.stderr}")
        return None
    except Exception as e:
        print(f"[warn] Unexpected error in probe_duration: {e}")
        return None


# ---------------------------------------------------------
# ✂️ استخراج مقطع من الفيديو
# ---------------------------------------------------------
def run_ffmpeg_extract_clip(src: Path, dst: Path, start: float, duration: float) -> None:
    """
    يقتطع مقطع من الفيديو باستخدام FFmpeg.
    """
    ensure_binaries()
    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        FFMPEG_PATH,
        "-y",                # الكتابة فوق الملفات
        "-ss", str(start),   # نقطة البداية
        "-i", str(src),      # ملف الإدخال
        "-t", str(duration), # المدة
        "-c", "copy",        # نسخ بدون إعادة ترميز
        str(dst)
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[ok] تم استخراج المقطع بنجاح: {dst}")
    except subprocess.CalledProcessError as e:
        print(f"[error] ffmpeg failed:\n{e.stderr.decode(errors='ignore') if hasattr(e.stderr, 'decode') else e}")
        raise
    except Exception as e:
        print(f"[error] Unexpected error in run_ffmpeg_extract_clip: {e}")
        raise


# ---------------------------------------------------------
# 📦 أداة مساعدة: نسخ ملف إلى مكان آخر (مثلاً عند حفظ نتائج)
# ---------------------------------------------------------
def copy_file(src: Path, dst: Path):
    """ينسخ ملفًا إلى وجهة محددة."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"[info] Copied: {src.name} → {dst}")
