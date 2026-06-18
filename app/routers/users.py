from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Announcement, User, UserRole

router = APIRouter(tags=["users"])


@router.get("/users/me/manager")
def my_manager(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.manager_id:
        return {"manager": None}
    mgr = db.query(User).filter(User.id == current_user.manager_id).first()
    if not mgr:
        return {"manager": None}
    return {
        "manager": {
            "id": mgr.id,
            "name": mgr.name,
            "email": mgr.email,
            "role": mgr.role.value,
            "department": mgr.department,
        }
    }


@router.get("/users/me/teammates")
def my_teammates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.manager_id:
        return []
    rows = (
        db.query(User)
        .filter(User.manager_id == current_user.manager_id, User.id != current_user.id)
        .all()
    )
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role.value, "department": u.department}
        for u in rows
    ]


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "department": u.department,
            "is_bookable_executive": u.is_bookable_executive,
            "manager_id": u.manager_id,
        }
        for u in users
    ]


@router.get("/users/me/team")
def my_team(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only managers/admin can view team")
    members = db.query(User).filter(User.manager_id == current_user.id).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "email": m.email,
            "role": m.role.value,
            "department": m.department,
        }
        for m in members
    ]


@router.get("/announcements")
def list_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return [{"id": a.id, "title": a.title, "body": a.body} for a in rows]
