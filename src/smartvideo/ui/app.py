import streamlit as st
import requests
import mimetypes
from pathlib import Path
from smartvideo.ui.components.html5_player import html5_player

def _get_api_base() -> str:
    """
    Retrieve the API base URL from Streamlit secrets, or fallback to localhost.

    Returns:
        str: API base URL.
    """
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return "http://127.0.0.1:8000"

API_BASE = _get_api_base()

st.set_page_config(page_title="Smart Video UI", layout="wide")
st.title("🎬 Smart Video Player — Local")

tab1, tab2 = st.tabs(["Upload & Play", "Extract Clip"])

with tab1:
    st.subheader("Upload and Play a Video")
    f = st.file_uploader("Choose a video file", type=["mp4", "mkv", "avi", "mov"])

    if st.button("Upload File", disabled=not f):
        if f:
            suffix = Path(f.name).suffix.lower().lstrip(".")
            mime = mimetypes.types_map.get(f".{suffix}", "application/octet-stream")
            files = {"file": (f.name, f, mime)}

            r = requests.post(f"{API_BASE}/upload", files=files, timeout=120)
            if r.ok:
                st.session_state["video_meta"] = r.json()
                st.success("Upload successful")
            else:
                st.error(r.text)

    if "video_meta" in st.session_state:
        meta = st.session_state["video_meta"]
        st.json(meta)

        filename = f"{meta['id']}{meta['ext']}"
        video_url = f"{API_BASE}/uploads/{filename}"
        # For better seek performance:
        # video_url = f"{API_BASE}/uploads/stream/{filename}"

        st.video(video_url)

with tab2:
    st.subheader("Extract a Clip (FFmpeg)")
    meta = st.session_state.get("video_meta")
    if not meta:
        st.info("Please upload a video first from the previous tab.")
    else:
        start = st.number_input("Clip start time (s)", min_value=0.0, value=0.0, step=0.5)
        duration = st.number_input("Clip duration (s)", min_value=0.1, value=5.0, step=0.5)
        if st.button("Extract Clip"):
            data = {
                "video_id": meta["id"],
                "ext": meta["ext"],
                "start": str(start),
                "duration": str(duration),
            }
            r = requests.post(f"{API_BASE}/extract", data=data, timeout=300)
            if r.ok:
                out = r.json()
                st.success("Clip created successfully")
                clip_url = f"{API_BASE}/outputs/{out['output']}"
                st.video(clip_url)
            else:
                st.error(r.text)