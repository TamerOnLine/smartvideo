<h1 align="center">🎬 SmartVideo — FastAPI + Streamlit Video Toolkit</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-1.39+-FF4B4B?logo=streamlit" alt="Streamlit">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 🧠 Overview

**SmartVideo** is a portable, all-in-one video processing toolkit built with **FastAPI** and **Streamlit**.  
It provides both a web API and an interactive UI for uploading, previewing, trimming, and analyzing videos —  
all powered by an embedded **FFmpeg** engine included with the package.

✅ **Key features**
- 🎥 Upload and preview videos instantly  
- ✂️ Extract video clips using precise start/duration  
- 🖼️ Generate thumbnails every N seconds  
- 🔊 Extract audio (MP3/WAV)  
- ⚙️ FastAPI backend + Streamlit frontend  
- 💾 Built-in portable `ffmpeg` and `ffprobe` binaries (no system install needed)

---

## 🚀 Quick Start

### 1️⃣ Installation

```bash
pip install smartvideo
```

*(Or locally if you're developing)*

```bash
uv pip install -e .
```

---

### 2️⃣ Run the FastAPI backend

```bash
uv run svapi
```

By default it starts at:  
➡️ **http://127.0.0.1:8000**

---

### 3️⃣ Run the Streamlit UI

```bash
uv run svui
```

Then open:  
➡️ **http://localhost:8501**

---

## 🧩 Project Structure

```
smartvideo/
├── bin/
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── sv/
│   ├── api.py            ← FastAPI backend
│   ├── cli.py            ← CLI entry points
│   └── core/
│       ├── config.py
│       └── services/
│           └── process.py
└── ui/
    ├── app.py            ← Streamlit interface
    └── components/
        └── html5_player.py
```

---

## ⚙️ Environment Configuration

SmartVideo automatically bundles `ffmpeg` and `ffprobe`,  
but you can override them via environment variables:

```bash
set SMARTVIDEO_FFMPEG=C:\Tools\ffmpeg.exe
set SMARTVIDEO_FFPROBE=C:\Tools\ffprobe.exe
```

or in Linux/macOS:
```bash
export SMARTVIDEO_FFMPEG=/usr/local/bin/ffmpeg
export SMARTVIDEO_FFPROBE=/usr/local/bin/ffprobe
```

---

## 🧪 API Endpoints (summary)

| Endpoint | Method | Description |
|-----------|---------|-------------|
| `/health` | GET | Health check |
| `/upload` | POST | Upload video |
| `/extract` | POST | Extract a video clip |
| `/thumbnails` | POST | Generate thumbnails every N seconds |
| `/audio` | POST | Extract audio (mp3/wav) |
| `/uploads/{filename}` | GET | Stream uploaded file |
| `/outputs/{filename}` | GET | Stream processed file |

---

## 💡 Developer Notes

### 🧩 Local Development

```bash
# 1️⃣ Sync dependencies
uv sync

# 2️⃣ Run the FastAPI backend
uv run svapi

# 3️⃣ Run the Streamlit UI
uv run svui
```

> ✨ After launch:  
> UI → http://localhost:8501  
> API → http://127.0.0.1:8000

### Testing

```bash
uv run pytest -v
```

---

## 📦 Packaging & Publishing

Build a wheel:

```bash
uv build
```

Publish to PyPI:

```bash
uv publish
```

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-------------|
| Backend | 🐍 FastAPI, Uvicorn |
| Frontend | 🎨 Streamlit |
| Media Processing | 🎞️ FFmpeg, MoviePy, OpenCV |
| Packaging | 🧱 Setuptools + uv |
| Testing | 🧪 Pytest, Httpx |
| Linting | ✨ Ruff |

---

## 🧑‍💻 Author

**Tamer Hamad Faour**  
📫 [GitHub](https://github.com/TamerOnLine) • [PyPI](https://pypi.org/user/TamerOnLine)

---

## 📜 License

Released under the **MIT License** — free for personal and commercial use.  
See [LICENSE](./LICENSE) for details.
