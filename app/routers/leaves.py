from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Leave, LeaveStatus, LeaveType, User, UserRole
from app.schemas import LeaveApprovalRequest, LeaveCreateRequest
from app.services.users import get_team_member_ids

router = APIRouter(tags=["leaves"])


@router.post("/leaves/request")
def request_leave(
    payload: LeaveCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target = db.query(User).filter(User.email == payload.user_email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER) and target.id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only request your own leave")
    if current_user.role == UserRole.MANAGER and target.manager_id != current_user.id and target.id != current_user.id:
        raise HTTPException(status_code=403, detail="Managers can request leave only for team")

    leave_type = LeaveType.LEAVE if payload.leave_type.lower() == "leave" else LeaveType.HOLIDAY
    leave = Leave(
        user_id=target.id,
        start_date=datetime.fromisoformat(f"{payload.start_date}T00:00:00"),
        end_date=datetime.fromisoformat(f"{payload.end_date}T23:59:59"),
        leave_type=leave_type,
        status=LeaveStatus.PENDING,
        reason=payload.reason,
        approved_by=None,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return {"success": True, "leave_id": leave.id, "status": leave.status.value}


@router.post("/leaves/review")
def review_leave(
    payload: LeaveApprovalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Only manager/admin can review leave")
    leave = db.query(Leave).filter(Leave.id == payload.leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    target = db.query(User).filter(User.id == leave.user_id).first()
    if current_user.role == UserRole.MANAGER and target and target.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Managers can review only team leave")
    if payload.action not in ("approve", "decline"):
        raise HTTPException(status_code=400, detail="action must be approve or decline")

    leave.status = LeaveStatus.APPROVED if payload.action == "approve" else LeaveStatus.DECLINED
    leave.approved_by = current_user.id
    db.commit()
    return {"success": True, "leave_id": leave.id, "status": leave.status.value}


@router.get("/leaves/pending")
def pending_leaves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        raise HTTPException(status_code=403, detail="Only manager/admin can view pending leave")
    query = db.query(Leave).filter(Leave.status == LeaveStatus.PENDING)
    if current_user.role == UserRole.MANAGER:
        team_ids = get_team_member_ids(db, current_user.id)
        query = query.filter(Leave.user_id.in_(team_ids + [current_user.id]))
    rows = query.order_by(Leave.created_at.desc()).all()
    users = {u.id: u for u in db.query(User).all()}
    return [
        {
            "id": r.id,
            "user": users[r.user_id].name if r.user_id in users else "Unknown",
            "user_email": users[r.user_id].email if r.user_id in users else "",
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "reason": r.reason,
        }
        for r in rows
    ]


@router.get("/leaves/upcoming")
def upcoming_leaves(
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    until = now + timedelta(days=days)
    query = db.query(Leave).filter(
        Leave.start_date <= until,
        Leave.end_date >= now,
        Leave.status == LeaveStatus.APPROVED,
    )

    if current_user.role == UserRole.ADMIN:
        rows = query.all()
    elif current_user.role == UserRole.MANAGER:
        team_ids = get_team_member_ids(db, current_user.id)
        rows = query.filter(Leave.user_id.in_(team_ids + [current_user.id])).all()
    else:
        rows = query.filter(Leave.user_id == current_user.id).all()

    users = {u.id: u for u in db.query(User).all()}
    return [
        {
            "id": r.id,
            "user": users[r.user_id].name if r.user_id in users else "Unknown",
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "type": r.leave_type.value,
            "status": r.status.value,
        }
        for r in rows
    ]
