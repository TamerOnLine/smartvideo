# 🎬 SmartVideo — FastAPI + Streamlit Video Toolkit

[![PyPI version](https://img.shields.io/pypi/v/smartvideo?color=blue&label=PyPI)](https://pypi.org/project/smartvideo/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](#)
[![CI](https://github.com/TamerOnLine/smartvideo/actions/workflows/ci.yml/badge.svg)](https://github.com/TamerOnLine/smartvideo/actions/workflows/ci.yml)
[![Publish](https://github.com/TamerOnLine/smartvideo/actions/workflows/publish.yml/badge.svg)](https://github.com/TamerOnLine/smartvideo/actions/workflows/publish.yml)

> **SmartVideo** — A modern, cross-platform video player and clip extractor built with **FastAPI**, **Streamlit**, and **FFmpeg**.  
> Upload, preview, trim, and stream videos — locally or via REST API.

---

## 🚀 Features

- ⚙️ **Auto FFmpeg/FFprobe detection & download** (Windows, macOS, Linux)
- 🌐 **FastAPI backend** with REST endpoints:
  - `/upload` — upload and probe duration
  - `/extract` — extract a clip (start + duration)
  - `/outputs/{file}` — serve generated clips
- 🖥️ **Streamlit UI**:
  - Drag-and-drop upload
  - HTML5 video preview player
  - Clip extraction via form controls
- 💡 **CLI tools**:
  - `svapi` → run backend server (FastAPI)
  - `svui` → run Streamlit UI
- 🔁 **Cross-platform binaries** — automatically downloaded if missing
- 🧱 Modular architecture (`sv/core`, `sv/ui`, `sv/api`)
- 🧪 Ready-to-use GitHub Actions for CI/CD and PyPI publishing

---

## 🧩 Project Structure

```
smartvideo/
├── src/smartvideo/
│   ├── sv/
│   │   ├── api.py         # FastAPI backend
│   │   ├── cli.py         # CLI launchers
│   │   └── core/
│   │       ├── config.py  # Data paths
│   │       └── services/process.py  # FFmpeg logic
│   └── ui/
│       ├── app.py         # Streamlit frontend
│       └── components/html5_player.py
├── data/uploads/          # Uploaded videos
├── data/outputs/          # Generated clips
├── tools/                 # Dev tools & publishing scripts
├── tests/                 # Basic tests
├── pyproject.toml         # Build metadata
├── CHANGELOG.md
└── LICENSE
```

---

## ⚡ Quick Start

### 1️⃣ Install

```bash
pip install smartvideo
```

Or for local development:

```bash
uv pip install -e .[dev]
```

---

### 2️⃣ Run the API (FastAPI)

```bash
svapi --port 8000
```

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

### 3️⃣ Run the UI (Streamlit)

```bash
svui --port 8501
```

Then open [http://localhost:8501](http://localhost:8501)

You can adjust upload size:
```bash
svui --max-upload-mb 4096
```

---

## 🔧 FFmpeg Setup

SmartVideo automatically downloads FFmpeg if missing.  
But you can install it manually:

### 🪟 Windows
```powershell
winget install Gyan.FFmpeg
# or
choco install ffmpeg
```

### 🍎 macOS
```bash
brew install ffmpeg
```

### 🐧 Linux
```bash
sudo apt install -y ffmpeg
```

Verify:
```bash
ffmpeg -version
ffprobe -version
```

---

## 🧠 API Endpoints

| Method | Endpoint | Description |
|---------|-----------|-------------|
| `GET` | `/health` | Check API status |
| `POST` | `/upload` | Upload video and get duration |
| `POST` | `/extract` | Extract video clip |
| `GET` | `/uploads/{filename}` | Serve uploaded video |
| `GET` | `/outputs/{filename}` | Serve generated clip |
| `GET` | `/uploads/stream/{filename}` | Stream with HTTP Range support |

---

## 🧪 Development

```bash
git clone https://github.com/TamerOnLine/smartvideo
cd smartvideo
uv sync --extra dev
uv run svapi
uv run svui
```

Run tests:
```bash
uv run pytest
```

---

## 🧰 GitHub Workflows

| Workflow | Purpose |
|-----------|----------|
| **ci.yml** | Runs tests, builds package, uploads artifacts |
| **publish.yml** | Trusted publishing to PyPI when tagging `v*.*.*` |

---

## 🗓️ Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.  
Example from v0.1.6:
- Added automatic FFmpeg download for Linux & macOS  
- Unified resolver and improved permission handling  
- Improved logging and cleanup routines

---

## 📜 License

Licensed under the [MIT License](LICENSE) © 2025 **TamerOnLine**

---

## 🌟 Roadmap

- 🧠 AI-powered video summarization & speech-to-text  
- 🎞️ Automatic scene detection & keyframe extraction  
- ☁️ Remote storage + REST streaming integration  
- 🧩 Web dashboard for managing clips and metadata  
