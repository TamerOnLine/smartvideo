import streamlit as st
import requests, mimetypes
from pathlib import Path
from ui.components.html5_player import html5_player

def _get_api_base() -> str:
    # يتحمل غياب secrets.toml
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return "http://127.0.0.1:8000"

API_BASE = _get_api_base()

st.set_page_config(page_title="Smart Video UI", layout="wide")
st.title("🎬 Smart Video Player — Local")

tab1, tab2 = st.tabs(["Upload & Play", "Extract Clip"])

with tab1:
    st.subheader("رفع فيديو وتشغيله")
    f = st.file_uploader("اختر ملف فيديو", type=["mp4","mkv","avi","mov"])

    if st.button("رفع الملف", disabled=not f):
        if f:
            # نوع MIME صحيح
            suffix = Path(f.name).suffix.lower().lstrip(".")
            mime = mimetypes.types_map.get(f".{suffix}", "application/octet-stream")
            files = {"file": (f.name, f, mime)}

            r = requests.post(f"{API_BASE}/upload", files=files, timeout=120)
            if r.ok:
                st.session_state["video_meta"] = r.json()
                st.success("تم الرفع")
            else:
                st.error(r.text)

    if "video_meta" in st.session_state:
        meta = st.session_state["video_meta"]
        st.json(meta)

        # 🔗 إنشاء رابط التشغيل الصحيح عبر الـAPI
        filename = f"{meta['id']}{meta['ext']}"
        # الخيار الأول: عرض عادي
        video_url = f"{API_BASE}/uploads/{filename}"
        # الخيار الثاني (أفضل في التقديم والتأخير):
        # video_url = f"{API_BASE}/uploads/stream/{filename}"

        # ✅ عرض الفيديو
        st.video(video_url)


with tab2:
    st.subheader("اقتطاع مقطع (FFmpeg)")
    meta = st.session_state.get("video_meta")
    if not meta:
        st.info("ارفع فيديو أولاً من التبويب السابق.")
    else:
        start = st.number_input("بداية المقطع (ث)", min_value=0.0, value=0.0, step=0.5)
        duration = st.number_input("المدة (ث)", min_value=0.1, value=5.0, step=0.5)
        if st.button("تنفيذ الاقتطاع"):
            data = {
                "video_id": meta["id"],
                "ext": meta["ext"],
                "start": str(start),
                "duration": str(duration),
            }
            r = requests.post(f"{API_BASE}/extract", data=data, timeout=300)
            if r.ok:
                out = r.json()
                st.success("تم إنشاء المقطع")
                clip_url = f"{API_BASE}/outputs/{out['output']}"
                st.video(clip_url)
            else:
                st.error(r.text)
