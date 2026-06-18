from datetime import datetime

from sqlalchemy.orm import Session

from app.models import (
    Meeting,
    MeetingAttendee,
    MeetingRequest,
    MeetingStatus,
    RequestStatus,
    User,
)
from app.services.availability import check_person_availability
from app.services.users import find_person_by_name


def create_meeting_request(
    db: Session,
    requester_name: str,
    target_person_name: str,
    reason: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    """Create a pending meeting request (employee → director/executive)."""
    requester = find_person_by_name(db, requester_name)
    if not requester:
        return {"success": False, "error": f"Requester '{requester_name}' not found"}

    target = find_person_by_name(db, target_person_name)
    if not target:
        return {"success": False, "error": f"Target person '{target_person_name}' not found"}

    if not target.is_bookable_executive:
        return {
            "success": False,
            "error": f"{target.name} is not set up for executive meeting requests",
        }

    availability = check_person_availability(db, target.name, start_time, end_time)

    request = MeetingRequest(
        requester_id=requester.id,
        target_person_id=target.id,
        reason=reason,
        proposed_start=start_time,
        proposed_end=end_time,
        status=RequestStatus.PENDING,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    delegate_name = None
    if target.delegate_user_id:
        delegate = db.query(User).filter(User.id == target.delegate_user_id).first()
        if delegate:
            delegate_name = delegate.name

    return {
        "success": True,
        "request_id": request.id,
        "status": "pending",
        "requester": requester.name,
        "target": target.name,
        "delegate": delegate_name,
        "target_available": availability["available"],
        "message": (
            f"Meeting request sent to {delegate_name or target.name} for approval."
            if not availability["available"]
            else f"Meeting request created. {target.name} appears available at that time."
        ),
    }


def draft_meeting_email(
    requester_name: str,
    target_person_name: str,
    reason: str,
    start_time: datetime,
    end_time: datetime,
    target_available: bool,
    conflicts: list | None = None,
) -> dict:
    """Draft a polite meeting request email."""
    date_str = start_time.strftime("%A, %B %d, %Y")
    time_str = f"{start_time.strftime('%I:%M %p')} – {end_time.strftime('%I:%M %p')}"

    subject = f"Meeting request: {reason[:50]}"

    if target_available:
        body = f"""Dear {target_person_name},

I hope this message finds you well.

I would like to request a meeting on {date_str} from {time_str} to discuss:

{reason}

Please let me know if this time works for you.

Best regards,
{requester_name}
"""
    else:
        conflict_note = ""
        if conflicts:
            titles = ", ".join(c["title"] for c in conflicts)
            conflict_note = f"\nI understand you may be occupied ({titles}). "

        body = f"""Dear {target_person_name},

I hope you are doing well.{conflict_note}
I would like to request a brief meeting on {date_str} around {time_str} regarding:

{reason}

If this time is not convenient, I would be grateful for any alternative slot you might suggest.

Thank you for your consideration.

Best regards,
{requester_name}
"""

    return {
        "to": target_person_name,
        "subject": subject,
        "body": body.strip(),
    }


def approve_meeting_request(db: Session, request: MeetingRequest) -> dict:
    """
    Approve a meeting request and block the executive's calendar.
    Creates a confirmed Meeting with requester and target as attendees.
    """
    if request.status != RequestStatus.PENDING:
        return {
            "success": False,
            "error": f"Request is already {request.status.value}",
        }

    target = db.query(User).filter(User.id == request.target_person_id).first()
    requester = db.query(User).filter(User.id == request.requester_id).first()
    if not target or not requester:
        return {"success": False, "error": "Requester or target user not found"}

    organizer_id = target.delegate_user_id or target.id

    meeting = Meeting(
        title=request.reason[:200] if request.reason else "Meeting",
        organizer_id=organizer_id,
        start_time=request.proposed_start,
        end_time=request.proposed_end,
        status=MeetingStatus.CONFIRMED,
    )
    db.add(meeting)
    db.flush()

    db.add(MeetingAttendee(meeting_id=meeting.id, user_id=target.id, is_required=True))
    db.add(MeetingAttendee(meeting_id=meeting.id, user_id=requester.id, is_required=True))

    request.status = RequestStatus.APPROVED
    db.commit()
    db.refresh(meeting)

    return {
        "success": True,
        "request_id": request.id,
        "meeting_id": meeting.id,
        "status": request.status.value,
    }


def decline_meeting_request(db: Session, request: MeetingRequest) -> dict:
    if request.status != RequestStatus.PENDING:
        return {
            "success": False,
            "error": f"Request is already {request.status.value}",
        }
    request.status = RequestStatus.DECLINED
    db.commit()
    return {"success": True, "request_id": request.id, "status": request.status.value}
