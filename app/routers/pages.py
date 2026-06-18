from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.paths import STATIC_DIR

router = APIRouter(tags=["pages"])


@router.get("/")
def root():
    page = STATIC_DIR / "home.html"
    if page.exists():
        return FileResponse(page)
    return {
        "message": "Office Copilot API is running",
        "dashboard": "/dashboard",
        "chat_ui": "/app",
        "docs": "/docs",
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/dashboard")
def dashboard_page():
    """Role-based dashboard with integrated Office Copilot."""
    page = STATIC_DIR / "dashboard.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Dashboard UI not found")
    return FileResponse(page)


@router.get("/app")
def chat_app():
    """Simple chat frontend."""
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Chat UI not found")
    return FileResponse(index)
