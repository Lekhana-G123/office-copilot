from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    Leave,
    LeaveStatus,
    Meeting,
    MeetingAttendee,
    MeetingStatus,
    User,
    UserRole,
)
from app.services.users import find_person_by_name


def is_on_approved_leave(
    db: Session, user_id: int, start_time: datetime, end_time: datetime
) -> bool:
    leaves = (
        db.query(Leave)
        .filter(
            Leave.user_id == user_id,
            Leave.status == LeaveStatus.APPROVED,
        )
        .all()
    )
    for leave in leaves:
        if leave.start_date <= end_time and leave.end_date >= start_time:
            return True
    return False


def check_person_availability(
    db: Session,
    person_name: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """
    Check if a person is available between start_time and end_time.
    Busy = they have a CONFIRMED meeting that overlaps this window.
    """
    person = find_person_by_name(db, person_name)
    if not person:
        return {
            "available": False,
            "person": person_name,
            "reason": "Person not found",
            "conflicts": [],
        }

    attendee_rows = (
        db.query(MeetingAttendee, Meeting)
        .join(Meeting, MeetingAttendee.meeting_id == Meeting.id)
        .filter(
            MeetingAttendee.user_id == person.id,
            Meeting.status == MeetingStatus.CONFIRMED,
        )
        .all()
    )

    conflicts = []
    for _attendee, meeting in attendee_rows:
        if meeting.start_time < end_time and meeting.end_time > start_time:
            conflicts.append({
                "title": meeting.title,
                "start": meeting.start_time.isoformat(),
                "end": meeting.end_time.isoformat(),
            })

    if conflicts:
        return {
            "available": False,
            "person": person.name,
            "person_id": person.id,
            "reason": "Has confirmed meeting(s) at this time",
            "conflicts": conflicts,
        }

    return {
        "available": True,
        "person": person.name,
        "person_id": person.id,
        "reason": "No conflicting meetings",
        "conflicts": [],
    }


def check_person_availability_for_viewer(
    db: Session,
    viewer: User,
    person_name: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """
    Privacy-aware availability:
    - Employee: own leave details only, others get free/busy.
    - Manager: team leave details visible.
    - Admin: everyone leave details visible.
    """
    base = check_person_availability(db, person_name, start_time, end_time)
    person = find_person_by_name(db, person_name)
    if not person:
        return base

    on_leave = is_on_approved_leave(db, person.id, start_time, end_time)
    if not on_leave:
        return base

    can_view_leave_reason = (
        viewer.role == UserRole.ADMIN
        or viewer.id == person.id
        or (viewer.role == UserRole.MANAGER and person.manager_id == viewer.id)
    )

    if can_view_leave_reason:
        return {
            "available": False,
            "person": person.name,
            "person_id": person.id,
            "reason": "On approved leave",
            "conflicts": [],
        }

    return {
        "available": False,
        "person": person.name,
        "person_id": person.id,
        "reason": "Not available",
        "conflicts": [],
    }
