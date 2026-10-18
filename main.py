import sys
from pathlib import Path

# Locate the repository root and backend directory.
ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "apps" / "backend"

# Make the backend's "app" package importable.
sys.path.insert(0, str(BACKEND_DIR))

# Export the existing FastAPI application for Vercel.
from app.main import app  # noqa: E402