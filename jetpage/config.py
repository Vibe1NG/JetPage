import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

CONTENT_DIR = Path(os.environ.get("CONTENT_DIR", BASE_DIR / "content"))
PORT = int(os.environ.get("PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")
