from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    Announcement,
    Leave,
    LeaveStatus,
    Meeting,
    MeetingAttendee,
    MeetingRequest,
    RequestStatus,
    Room,
    RoomBooking,
    Task,
    TaskStatus,
    User,
    UserRole,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me")
def my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rooms_by_id = {r.id: r.name for r in db.query(Room).all()}
    my_tasks = db.query(Task).filter(Task.assignee_id == current_user.id).all()
    my_room_bookings = (
        db.query(RoomBooking)
        .filter(RoomBooking.booked_by_id == current_user.id)
        .order_by(RoomBooking.start_time.asc())
        .limit(10)
        .all()
    )
    meeting_rows = (
        db.query(Meeting)
        .join(MeetingAttendee, MeetingAttendee.meeting_id == Meeting.id)
        .filter(MeetingAttendee.user_id == current_user.id)
        .order_by(Meeting.start_time.asc())
        .limit(10)
        .all()
    )
    my_upcoming_leave = (
        db.query(Leave)
        .filter(
            Leave.user_id == current_user.id,
            Leave.end_date >= datetime.utcnow(),
        )
        .order_by(Leave.start_date.asc())
        .all()
    )
    return {
        "user": {"name": current_user.name, "role": current_user.role.value},
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in my_tasks
        ],
        "meetings": [
            {
                "id": m.id,
                "title": m.title,
                "start": m.start_time.isoformat(),
                "end": m.end_time.isoformat(),
                "status": m.status.value,
                "room": rooms_by_id.get(m.room_id) if m.room_id else None,
            }
            for m in meeting_rows
        ],
        "room_bookings": [
            {
                "id": b.id,
                "title": b.title,
                "start": b.start_time.isoformat(),
                "end": b.end_time.isoformat(),
                "room": rooms_by_id.get(b.room_id),
            }
            for b in my_room_bookings
        ],
        "upcoming_leaves": [
            {
                "id": l.id,
                "start": l.start_date.isoformat(),
                "end": l.end_date.isoformat(),
                "status": l.status.value,
                "type": l.leave_type.value,
            }
            for l in my_upcoming_leave
        ],
    }


@router.get("/team")
def team_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only manager/admin can view team dashboard")
    members = db.query(User).filter(User.manager_id == current_user.id).all()
    member_ids = [m.id for m in members]

    team_tasks = db.query(Task).filter(Task.assignee_id.in_(member_ids)).all() if member_ids else []
    overdue = [
        t for t in team_tasks
        if t.due_date and t.due_date < datetime.utcnow() and t.status != TaskStatus.DONE
    ]
    team_meeting_count = (
        db.query(func.count(MeetingAttendee.id))
        .filter(MeetingAttendee.user_id.in_(member_ids))
        .scalar()
        if member_ids else 0
    )
    return {
        "manager": current_user.name,
        "team_members": [
            {"id": m.id, "name": m.name, "email": m.email, "department": m.department}
            for m in members
        ],
        "task_summary": {
            "open": len([t for t in team_tasks if t.status == TaskStatus.OPEN]),
            "in_progress": len([t for t in team_tasks if t.status == TaskStatus.IN_PROGRESS]),
            "done": len([t for t in team_tasks if t.status == TaskStatus.DONE]),
            "overdue": len(overdue),
        },
        "team_meeting_load": team_meeting_count,
        "behind_schedule": [
            {"task_id": t.id, "title": t.title, "assignee_id": t.assignee_id}
            for t in overdue
        ],
    }


@router.get("/director")
def director_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.EXECUTIVE, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Only executive/admin can view director dashboard")
    tasks = db.query(Task).all()
    users = db.query(User).all()
    users_by_id = {u.id: u for u in users}
    by_department: dict[str, dict[str, int]] = {}
    for task in tasks:
        user = users_by_id.get(task.assignee_id)
        dept = user.department if user else "Unknown"
        if dept not in by_department:
            by_department[dept] = {"open": 0, "in_progress": 0, "done": 0}
        by_department[dept][task.status.value] += 1

    major_meetings = (
        db.query(Meeting)
        .order_by(Meeting.start_time.desc())
        .limit(10)
        .all()
    )
    return {
        "viewer": current_user.name,
        "tasks_by_department": by_department,
        "major_meetings": [
            {
                "id": m.id,
                "title": m.title,
                "start": m.start_time.isoformat(),
                "end": m.end_time.isoformat(),
            }
            for m in major_meetings
        ],
    }


@router.get("/hr")
def hr_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only HR/admin can view HR dashboard")
    users = db.query(User).all()
    roles: dict[str, int] = {}
    for u in users:
        roles[u.role.value] = roles.get(u.role.value, 0) + 1
    pending_meeting_requests = db.query(MeetingRequest).filter(MeetingRequest.status == RequestStatus.PENDING).count()
    pending_leave_requests = db.query(Leave).filter(Leave.status == LeaveStatus.PENDING).count()
    return {
        "total_users": len(users),
        "users_by_role": roles,
        "rooms": db.query(Room).count(),
        "announcements": db.query(Announcement).count(),
        "pending_meeting_requests": pending_meeting_requests,
        "pending_leave_requests": pending_leave_requests,
    }
