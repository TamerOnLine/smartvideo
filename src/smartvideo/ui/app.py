# -*- coding: utf-8 -*-
"""
app.py — Streamlit UI for SmartVideo
------------------------------------
Upload, preview, and extract clips using SmartVideo API.

- Communicates with FastAPI backend (svapi).
- No FastAPI inside the UI — pure Streamlit.
- Supports up to 2 GB upload (configurable).
"""

import streamlit as st
import requests
import mimetypes
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
def _get_api_base() -> str:
    """Return SmartVideo API base URL (fallback to localhost)."""
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return "http://127.0.0.1:8000"

API_BASE = _get_api_base()
MAX_UPLOAD_MB = 2048

st.set_page_config(page_title="🎬 Smart Video Player", layout="wide")
st.title("🎬 Smart Video Player — Local")
st.caption(f"Max upload size: {MAX_UPLOAD_MB} MB")

# -----------------------------------------------------------------------------
# Tabs
# -----------------------------------------------------------------------------
tab1, tab2 = st.tabs(["📤 Upload & Play", "✂️ Extract Clip"])

# -----------------------------------------------------------------------------
# Tab 1 — Upload & Play
# -----------------------------------------------------------------------------
with tab1:
    st.subheader("Upload and Preview Video")
    f = st.file_uploader(
        "Choose a video file",
        type=["mp4", "mkv", "avi", "mov"],
        help=f"Maximum {MAX_UPLOAD_MB} MB",
    )

    if st.button("🚀 Upload", disabled=not f):
        if f:
            suffix = Path(f.name).suffix.lower().lstrip(".")
            mime = mimetypes.types_map.get(f".{suffix}", "application/octet-stream")
            files = {"file": (f.name, f, mime)}

            try:
                with st.spinner("Uploading and processing…"):
                    # ↑ Use long timeout to allow FFmpeg warm-up on first use
                    r = requests.post(f"{API_BASE}/upload", files=files, timeout=(10, 900))
                if r.ok:
                    st.session_state["video_meta"] = r.json()
                    st.success("✅ Upload successful!")
                    st.video(f"{API_BASE}/uploads/{Path(r.json()['path']).name}")
                else:
                    st.error(f"❌ Upload failed: {r.status_code} {r.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

# -----------------------------------------------------------------------------
# Tab 2 — Extract Clip
# -----------------------------------------------------------------------------
with tab2:
    st.subheader("Extract Clip")
    if "video_meta" not in st.session_state:
        st.info("Upload a video first from the previous tab.")
    else:
        meta = st.session_state["video_meta"]
        dur = float(meta.get("duration", 0))
        st.write(f"🎞️ Video duration: **{dur:.1f} s**")

        start = st.number_input("Start (seconds)", min_value=0.0, max_value=max(0.0, dur - 1), value=0.0, step=0.5)
        end = st.number_input("End (seconds)", min_value=0.0, max_value=dur, value=min(5.0, dur), step=0.5)
        reencode = st.checkbox("Re-encode (slower, compatible)")

        if st.button("✂️ Extract Clip"):
            try:
                with st.spinner("Processing clip…"):
                    data = {
                        "video_id": meta["id"],
                        "ext": meta["ext"],
                        "start": start,
                        "duration": end - start,
                        "reencode": reencode,
                    }
                    r = requests.post(f"{API_BASE}/extract", data=data, timeout=(10, 900))
                if r.ok:
                    out = r.json()
                    st.success("✅ Clip ready!")
                    st.video(f"{API_BASE}/outputs/{out['output']}")
                else:
                    st.error(f"❌ Extraction failed: {r.status_code} {r.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("© 2025 TamerOnLine — SmartVideo UI powered by Streamlit")
