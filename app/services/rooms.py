from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Meeting, MeetingAttendee, MeetingStatus, Room, RoomBooking
from app.services.users import find_person_by_name


def check_room_availability(
    db: Session,
    room_name: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    room = find_room_by_name(db, room_name)
    if not room:
        return {
            "available": False,
            "room": room_name,
            "reason": "Room not found",
            "conflicts": [],
        }

    bookings = (
        db.query(RoomBooking)
        .filter(RoomBooking.room_id == room.id)
        .all()
    )

    conflicts = []
    for booking in bookings:
        if booking.start_time < end_time and booking.end_time > start_time:
            conflicts.append({
                "title": booking.title,
                "start": booking.start_time.isoformat(),
                "end": booking.end_time.isoformat(),
            })

    if conflicts:
        return {
            "available": False,
            "room": room.name,
            "room_id": room.id,
            "capacity": room.capacity,
            "reason": "Room already booked at this time",
            "conflicts": conflicts,
        }

    return {
        "available": True,
        "room": room.name,
        "room_id": room.id,
        "capacity": room.capacity,
        "reason": "Room is free",
        "conflicts": [],
    }


def find_room_by_name(db: Session, name: str) -> Room | None:
    """Match room by exact name, 'Room X' suffix, or unambiguous substring."""
    name_lower = name.lower().strip()
    if not name_lower:
        return None

    rooms = db.query(Room).all()

    for room in rooms:
        if room.name.lower() == name_lower:
            return room

    for room in rooms:
        rn = room.name.lower()
        if rn.endswith(f" {name_lower}") or rn.endswith(name_lower):
            return room

    if name_lower.startswith("room "):
        suffix = name_lower[5:].strip()
        for room in rooms:
            rn = room.name.lower()
            if rn.endswith(suffix) or rn.endswith(f"room {suffix}"):
                return room

    if len(name_lower) >= 3:
        matches = [r for r in rooms if name_lower in r.name.lower()]
        if len(matches) == 1:
            return matches[0]
        if matches:
            return min(matches, key=lambda r: len(r.name))

    return None


def list_rooms(db: Session) -> dict:
    rooms = db.query(Room).all()
    return {
        "rooms": [
            {
                "id": r.id,
                "name": r.name,
                "capacity": r.capacity,
                "type": r.room_type,
            }
            for r in rooms
        ]
    }


def book_room(
    db: Session,
    booker_name: str,
    room_name: str,
    title: str,
    start_time: datetime,
    end_time: datetime,
) -> dict:
    booker = find_person_by_name(db, booker_name)
    if not booker:
        return {"success": False, "error": f"Booker '{booker_name}' not found"}

    room = find_room_by_name(db, room_name)
    if not room:
        return {"success": False, "error": f"Room '{room_name}' not found"}

    availability = check_room_availability(db, room.name, start_time, end_time)
    if not availability["available"]:
        return {
            "success": False,
            "error": "Room is not available at that time",
            "conflicts": availability["conflicts"],
        }

    booking = RoomBooking(
        room_id=room.id,
        booked_by_id=booker.id,
        title=title,
        start_time=start_time,
        end_time=end_time,
    )
    db.add(booking)
    db.flush()

    meeting = Meeting(
        title=f"{title} — {room.name}",
        organizer_id=booker.id,
        room_id=room.id,
        start_time=start_time,
        end_time=end_time,
        status=MeetingStatus.CONFIRMED,
    )
    db.add(meeting)
    db.flush()
    db.add(MeetingAttendee(meeting_id=meeting.id, user_id=booker.id, is_required=True))

    db.commit()
    db.refresh(booking)

    return {
        "success": True,
        "booking_id": booking.id,
        "room": room.name,
        "booked_by": booker.name,
        "title": title,
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "message": f"{room.name} booked successfully.",
    }
