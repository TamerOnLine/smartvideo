# -*- coding: utf-8 -*-
"""
api.py - FastAPI backend for Smart Video Player
-----------------------------------------------
Handles:
- File uploads
- Duration analysis (ffprobe)
- Clip extraction (ffmpeg)
- Serving video files (FileResponse / StreamingResponse)
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pathlib import Path
import shutil
import uuid
import os

# Internal paths
from smartvideo.sv.core.config import UPLOADS_DIR, OUTPUTS_DIR
from smartvideo.sv.core.services.process import run_ffmpeg_extract_clip, probe_duration

# -------------------------------------------------------------
# App setup
# -------------------------------------------------------------
app = FastAPI(title="Smart Video API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Consider restricting this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Health check endpoint
# -------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------------------------------------
# Video upload endpoint
# -------------------------------------------------------------
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in {".mp4", ".mkv", ".avi", ".mov"}:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    vid_id = uuid.uuid4().hex
    dest = UPLOADS_DIR / f"{vid_id}{ext}"

    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    dur = probe_duration(dest)
    return {"id": vid_id, "path": str(dest), "duration": dur, "ext": ext}

# -------------------------------------------------------------
# Clip extraction endpoint
# -------------------------------------------------------------
@app.post("/extract")
def extract_clip(
    video_id: str = Form(...),
    ext: str = Form(".mp4"),
    start: float = Form(...),
    duration: float = Form(...)
):
    src = UPLOADS_DIR / f"{video_id}{ext}"
    if not src.exists():
        raise HTTPException(status_code=404, detail="Source video not found.")

    out_name = f"{video_id}_clip_{start}_{duration}.mp4"
    dst = OUTPUTS_DIR / out_name
    run_ffmpeg_extract_clip(src, dst, start, duration)

    return {"output": out_name, "path": str(dst)}

# -------------------------------------------------------------
# Serve generated clips
# -------------------------------------------------------------
@app.get("/outputs/{filename}")
def get_output(filename: str):
    fp = OUTPUTS_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(fp, media_type="video/mp4")

# -------------------------------------------------------------
# Serve uploaded videos
# -------------------------------------------------------------
@app.get("/uploads/{filename}")
def get_upload(filename: str):
    fp = UPLOADS_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(fp, media_type="video/mp4")

# -------------------------------------------------------------
# Stream uploaded videos (supports range requests)
# -------------------------------------------------------------
@app.get("/uploads/stream/{filename}")
def stream_upload(filename: str, request: Request):
    fp = UPLOADS_DIR / filename
    if not fp.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    range_header = request.headers.get("range")
    file_size = os.path.getsize(fp)
    start = 0
    end = file_size - 1

    if range_header:
        _, rng = range_header.split("=")
        parts = rng.split("-")
        start = int(parts[0]) if parts[0] else 0
        if len(parts) > 1 and parts[1]:
            end = int(parts[1])
        start = max(0, start)
        end = min(end, file_size - 1)

    def iterfile(path, start_pos, end_pos, chunk_size=1024 * 1024):
        with open(path, "rb") as f:
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