from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import MeetingRequest, User, UserRole
from app.schemas import DraftEmailRequest, MeetingRequestCreate
from app.services.availability import check_person_availability_for_viewer
from app.services.meetings import (
    approve_meeting_request,
    create_meeting_request,
    decline_meeting_request,
    draft_meeting_email,
)
from app.services.rooms import check_room_availability, list_rooms

router = APIRouter(tags=["meetings"])


@router.get("/availability")
def get_availability(
    person: str,
    date: str,
    start_hour: int = 14,
    end_hour: int = 15,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_time = datetime.fromisoformat(f"{date}T{start_hour:02d}:00:00")
    end_time = datetime.fromisoformat(f"{date}T{end_hour:02d}:00:00")
    return check_person_availability_for_viewer(
        db, current_user, person, start_time, end_time
    )


@router.get("/rooms")
def get_rooms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_rooms(db)


@router.get("/rooms/availability")
def get_room_availability(
    room: str,
    date: str,
    start_hour: int = 10,
    end_hour: int = 11,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_time = datetime.fromisoformat(f"{date}T{start_hour:02d}:00:00")
    end_time = datetime.fromisoformat(f"{date}T{end_hour:02d}:00:00")
    return check_room_availability(db, room, start_time, end_time)


@router.post("/meeting-requests")
def post_meeting_request(
    payload: MeetingRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_time = datetime.fromisoformat(f"{payload.date}T{payload.start_hour:02d}:00:00")
    end_time = datetime.fromisoformat(f"{payload.date}T{payload.end_hour:02d}:00:00")
    return create_meeting_request(
        db,
        current_user.name,
        payload.target_person_name,
        payload.reason,
        start_time,
        end_time,
    )


@router.get("/meeting-requests")
def list_meeting_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = db.query(MeetingRequest).order_by(MeetingRequest.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "requester_id": r.requester_id,
            "target_person_id": r.target_person_id,
            "reason": r.reason,
            "proposed_start": r.proposed_start.isoformat(),
            "proposed_end": r.proposed_end.isoformat(),
            "status": r.status.value,
        }
        for r in rows
    ]


@router.post("/meeting-requests/review")
def review_meeting_request(
    request_id: int,
    action: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.ADMIN, UserRole.EA):
        raise HTTPException(status_code=403, detail="Only admin/EA can review requests")
    req = db.query(MeetingRequest).filter(MeetingRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Meeting request not found")
    if action not in ("approve", "decline"):
        raise HTTPException(status_code=400, detail="action must be approve or decline")

    if action == "approve":
        result = approve_meeting_request(db, req)
    else:
        result = decline_meeting_request(db, req)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Review failed"))
    return result


@router.post("/draft-email")
def post_draft_email(
    payload: DraftEmailRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_time = datetime.fromisoformat(f"{payload.date}T{payload.start_hour:02d}:00:00")
    end_time = datetime.fromisoformat(f"{payload.date}T{payload.end_hour:02d}:00:00")
    availability = check_person_availability_for_viewer(
        db, current_user, payload.target_person_name, start_time, end_time
    )
    return draft_meeting_email(
        current_user.name,
        payload.target_person_name,
        payload.reason,
        start_time,
        end_time,
        availability["available"],
        availability.get("conflicts"),
    )
