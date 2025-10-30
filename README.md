
## 🔧 Install FFmpeg (Windows / macOS / Linux)

SmartVideo requires **FFmpeg**.  
If it's not installed, use one of the following one-liners based on your OS:

### 🪟 Windows (PowerShell)
```powershell
winget install Gyan.FFmpeg
```
Alternative:
```powershell
choco install ffmpeg
```

### 🍎 macOS
```bash
brew install ffmpeg
```

### 🐧 Linux (Debian/Ubuntu)
```bash
sudo apt update && sudo apt install -y ffmpeg
```
Other distros:
```bash
sudo dnf install ffmpeg        # Fedora
sudo pacman -S ffmpeg          # Arch
```

### ✅ Verify installation
```bash
ffmpeg -version
ffprobe -version
```