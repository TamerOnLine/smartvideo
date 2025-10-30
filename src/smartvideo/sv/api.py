# -*- coding: utf-8 -*-
"""
api.py — FastAPI backend for SmartVideo
---------------------------------------
Features:
- Lifespan warm-up: ensure FFmpeg/FFprobe ready (auto-download on Windows once).
- Upload video (chunked write) + probe duration (ffprobe).
- Extract clip (ffmpeg) with start/duration.
- Serve and stream files (HTTP Range support).
"""

from __future__ import annotations

import os
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

# Internal imports
from smartvideo.sv.core.config import UPLOADS_DIR, OUTPUTS_DIR
from smartvideo.sv.core.services.process import (
    ensure_binaries,
    run_ffmpeg_extract_clip,
    probe_duration,
)

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
log = logging.getLogger("smartvideo")

# -----------------------------------------------------------------------------
# Lifespan (startup/shutdown) — modern replacement for on_event()
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        ffmpeg, ffprobe = ensure_binaries()
        log.info(f"Warmup OK: ffmpeg={ffmpeg}, ffprobe={ffprobe}")
    except Exception as e:
        log.error(f"Warmup failed: {e}")
    yield
    # Shutdown (currently nothing to cleanup)


# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title="Smart Video API",
    version="0.1.5",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج يمكن تقييدها
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Health + warmup endpoints
# -----------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/warmup")
def warmup():
    ffmpeg, ffprobe = ensure_binaries()
    return JSONResponse({"ffmpeg": ffmpeg, "ffprobe": ffprobe, "status": "ready"})


# -----------------------------------------------------------------------------
# Upload (chunked) + probe duration
# -----------------------------------------------------------------------------
ALLOWED_EXTS = {".mp4", ".mkv", ".avi", ".mov"}


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    vid_id = uuid.uuid4().hex
    dest = UPLOADS_DIR / f"{vid_id}{ext}"
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out, length=1024 * 1024)  # 1 MB chunks
    finally:
        try:
            await file.close()
        except Exception:
            pass

    try:
        dur = probe_duration(dest)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"FFmpeg not ready: {e}") from e

    return {"id": vid_id, "path": str(dest), "duration": dur, "ext": ext}


# -----------------------------------------------------------------------------
# Clip extraction
# -----------------------------------------------------------------------------
@app.post("/extract")
def extract_clip(
    video_id: str = Form(...),
    ext: str = Form(".mp4"),
    start: float = Form(...),
    duration: float = Form(...),
    reencode: Optional[bool] = Form(False),
):
    src = UPLOADS_DIR / f"{video_id}{ext}"
    if not src.exists():
        raise HTTPException(status_code=404, detail="Source video not found.")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_name = f"{video_id}_clip_{max(0, int(start))}_{max(0, int(duration))}.mp4"
    dst = OUTPUTS_DIR / out_name

    try:
        run_ffmpeg_extract_clip(
            src,
            dst,
            start=float(start),
            end=float(start + duration),
            codec_copy=not bool(reencode),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ffmpeg failed: {e}") from e

    return {"output": out_name, "path": str(dst)}


# -----------------------------------------------------------------------------
# Serve generated clips
# -----------------------------------------------------------------------------
@app.get("/outputs/{filename}")
def get_output(filename: str):
    fp = OUTPUTS_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(fp, media_type="video/mp4")


# -----------------------------------------------------------------------------
# Serve uploaded videos
# -----------------------------------------------------------------------------
@app.get("/uploads/{filename}")
def get_upload(filename: str):
    fp = UPLOADS_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(fp, media_type="video/mp4")


# -----------------------------------------------------------------------------
# Stream with Range support
# -----------------------------------------------------------------------------
@app.get("/uploads/stream/{filename}")
def stream_upload(filename: str, request: Request):
    fp = UPLOADS_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    file_size = os.path.getsize(fp)
    range_header = request.headers.get("range")
    start = 0
    end = file_size - 1

    if range_header:
        try:
            _, rng = range_header.split("=")
            s, _, e = rng.partition("-")
            if s:
                start = max(0, int(s))
            if e:
                end = min(file_size - 1, int(e))
        except Exception:
            start, end = 0, file_size - 1

    def iterfile(path: Path, start_pos: int, end_pos: int, chunk_size: int = 1024 * 1024):
        with path.open("rb") as f:
            f.seek(start_pos)
            remaining = end_pos - start_pos + 1
            while remaining > 0:
                data = f.read(min(chunk_size, remaining))
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
        "Content-Type": "video/mp4",
    }
    status = 206 if range_header else 200
    return StreamingResponse(iterfile(fp, start, end), status_code=status, headers=headers)
