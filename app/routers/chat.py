from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agent import run_agent
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ChatRequest

router = APIRouter(tags=["chat"])


@router.post("/chat")
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Chat with the AI agent. Must be logged in — uses your account automatically."""
    try:
        return run_agent(db, payload.message, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}",
        ) from e
