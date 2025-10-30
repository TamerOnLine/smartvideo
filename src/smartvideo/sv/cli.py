import uvicorn
from pathlib import Path
import os

def run_api():
    uvicorn.run("smartvideo.sv.api:app", host="127.0.0.1", port=8000, reload=True)

def run_ui():
    app_path = Path(__file__).resolve().parents[1] / "ui" / "app.py"
    os.execvp("streamlit", ["streamlit", "run", str(app_path), "--server.port", "8501"])
