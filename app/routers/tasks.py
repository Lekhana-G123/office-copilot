from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import TaskAssignRequest
from app.services.tasks import assign_task_to_user
from app.utils.dates import parse_due_date

router = APIRouter(tags=["tasks"])


@router.post("/tasks/assign")
def assign_task(
    payload: TaskAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assignee = db.query(User).filter(User.email == payload.assignee_email).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    try:
        due_dt = parse_due_date(payload.due_date)
        task = assign_task_to_user(
            db,
            current_user,
            assignee,
            payload.title,
            payload.description,
            payload.priority,
            due_dt,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    return {"success": True, "task_id": task.id, "assignee": assignee.name}
