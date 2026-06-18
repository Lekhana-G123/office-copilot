from pathlib import Path

# app/paths.py → app/ → project root (office-copilot/)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"