# 📜 Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.1] - 2025-10-30
### Added
- English-language PEP 8–compliant docstrings and comments for all core CLI and config functions.
- Automatic directory creation logic on first import of the config module.
- CLI flags for `--port` and `--max-upload-mb` in the `svui` command.

### Changed
- Replaced all Arabic comments and strings with English to maintain consistency and accessibility.
- Refactored CLI argument parsing for clarity and maintainability.

### Fixed
- Corrected fallback logic for `STREAMLIT_SERVER_MAX_UPLOAD_SIZE` environment variable when not provided.

---

## [0.1.0] - 2025-10-30
### Added
- 🎬 Initial public release of **SmartVideo** — FastAPI + Streamlit video toolkit.
- Added integrated **FFmpeg/FFprobe** portable binaries inside the package.
- Implemented FastAPI backend with:
  - `/upload` endpoint for video upload.
  - `/extract` for clip extraction.
  - `/thumbnails` for generating frame previews.
  - `/audio` for audio extraction (mp3/wav).
- Added Streamlit frontend with:
  - HTML5 player component.
  - Video upload, preview, and control interface.
- CLI commands:
  - `svapi` → runs the FastAPI backend.
  - `svui` → runs the Streamlit UI.
- Added `process.py` core service for FFmpeg integration.
- Bundled cross-platform support (Windows/Linux/macOS).

### Changed
- Project renamed from `smart-video` → `smartvideo` for PyPI compatibility.
- Internal imports updated to `smartvideo.sv.*`.
- Unified folder structure under `src/smartvideo/`.

### Fixed
- Resolved missing module errors when packaging (`ModuleNotFoundError: sv`).
- Corrected Streamlit import paths (`smartvideo.ui.components.html5_player`).
- Fixed missing FFmpeg detection logic on non-Windows systems.

---

## [Unreleased]
### Planned
- 🧠 Add AI-based video summarization and speech-to-text analysis.
- 🎞️ Add automatic scene detection and keyframe extraction.
- ☁️ Implement REST file streaming and remote storage integration.
