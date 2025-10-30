from pathlib import Path

# Define the root directory based on the script's location
ROOT = Path(__file__).resolve().parents[3]  # smart-video/

# Define paths for data storage
DATA_DIR = ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"

# Create the necessary directories if they do not exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)