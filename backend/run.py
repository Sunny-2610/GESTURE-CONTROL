"""Convenience launcher: python backend/run.py"""
import faulthandler
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
faulthandler.enable()

from app.main import run  # noqa: E402

if __name__ == "__main__":
    run(
        host=os.environ.get("GESTURE_HOST", "127.0.0.1"),
        port=int(os.environ.get("GESTURE_PORT", "8000")),
    )
