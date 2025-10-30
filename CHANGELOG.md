# 📜 Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## [0.1.2] - 2025-10-30
### Added
- Added automated PyPI publishing workflow via GitHub Actions (Trusted Publishing).
- Added optional FFmpeg auto-download step in CI to embed binaries inside the package.
- Included `uv build` + `uv publish` integration for reproducible releases.
- Added version and build information logging in CI for easier debugging.

### Changed
- Switched to `actions/setup-python@v5` for cleaner VS Code validation (no warnings).
- Simplified release workflow triggers (`release`, `push tags`, and `manual run` combined).
- Improved project structure for cross-platform packaging consistency.

### Fixed
- Removed invalid VS Code YAML warnings (`python-version` / `python` input issues).
- Ensured FFmpeg binaries are correctly detected and packaged in build artifacts.

---


## [0.1.1] - 2025-10-30
### Added
- Automatic creation of runtime folders (`data/uploads`, `data/outputs`) on first launch.
- Environment variable `SMARTVIDEO_DATA_DIR` for custom storage path.
- Unified CLI launcher (`svui`, `svapi`) with dynamic upload-size control.
- Config system (`sv/core/config.py`) for consistent data paths.

### Changed
- Moved `.streamlit/` folder to project root for proper Streamlit detection.
- Adopted `src/` layout for cleaner packaging and import safety.
- Simplified `pyproject.toml` with consolidated `package-data` section.

### Fixed
- Upload limit error (“File must be 200 MB or smaller”) removed permanently.
- API import path corrected (`smartvideo.sv.api:app`).
- Removed redundant platformdirs dependency for lighter package size.

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
