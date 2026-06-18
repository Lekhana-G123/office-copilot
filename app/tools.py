"""Backward-compatible re-exports. Prefer importing from app.services.* directly."""

from app.services.availability import (
    check_person_availability,
    check_person_availability_for_viewer,
    is_on_approved_leave,
)
from app.services.meetings import create_meeting_request, draft_meeting_email
from app.services.rooms import book_room, check_room_availability, find_room_by_name, list_rooms
from app.services.users import find_person_by_name, get_team_member_ids

__all__ = [
    "book_room",
    "check_person_availability",
    "check_person_availability_for_viewer",
    "check_room_availability",
    "create_meeting_request",
    "draft_meeting_email",
    "find_person_by_name",
    "find_room_by_name",
    "get_team_member_ids",
    "is_on_approved_leave",
    "list_rooms",
]
