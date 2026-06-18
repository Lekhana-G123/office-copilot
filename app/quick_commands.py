"""Run common commands directly without LLM — more reliable on Groq free tier."""

import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.services.availability import check_person_availability_for_viewer
from app.services.rooms import book_room, list_rooms
from app.services.tasks import (
    assign_task_to_user,
    format_my_tasks,
    format_team_status,
    get_my_tasks,
)
from app.services.users import find_person_by_name
from app.utils.dates import parse_due_date, parse_hour_range, resolve_date, today_str, tomorrow_str

_TODAY_STR = today_str()


def _normalize(text: str) -> str:
    return (
        text.lower()
        .replace("aviavle", "available")
        .replace("availble", "available")
        .replace("availabe", "available")
        .strip()
    )


def _resolve_person_name(db: Session, person: str) -> str:
    """Map shorthand like 'director' to a real executive in the directory."""
    p = person.strip().lower()
    if p in ("director", "the director", "our director"):
        execs = (
            db.query(User)
            .filter(User.role == UserRole.EXECUTIVE, User.is_bookable_executive.is_(True))
            .all()
        )
        for executive in execs:
            if "kumar" in executive.name.lower():
                return executive.name
        if execs:
            return execs[0].name
    return person.strip()


def _availability_reply(
    db: Session,
    user: User,
    person_raw: str,
    rest: str,
    *,
    default_date: str = _TODAY_STR,
) -> dict:
    person = _resolve_person_name(db, person_raw)
    date_token = default_date
    if "tomorrow" in rest:
        date_token = "tomorrow"
    elif "today" in rest:
        date_token = "today"
    elif re.search(r"\d{4}-\d{2}-\d{2}", rest):
        date_token = re.search(r"\d{4}-\d{2}-\d{2}", rest).group(0)
    try:
        date = resolve_date(date_token)
    except ValueError:
        date = _TODAY_STR
    start_hour, end_hour = parse_hour_range(rest)
    start_time = datetime.fromisoformat(f"{date}T{start_hour:02d}:00:00")
    end_time = datetime.fromisoformat(f"{date}T{end_hour:02d}:00:00")
    result = check_person_availability_for_viewer(db, user, person, start_time, end_time)
    if result.get("available"):
        reply = f"{result.get('person')} is available ({start_hour}:00–{end_hour}:00 on {date})."
    else:
        reply = f"{result.get('person')} is not available. Reason: {result.get('reason')}"
    return {"reply": reply, "tool_calls": [{"tool": "check_availability", "result": result}]}


def try_quick_command(db: Session, user: User, message: str) -> dict | None:
    text = _normalize(message)

    if text in ("okay", "ok", "thanks", "thank you", "cool", "great", "hi", "hello"):
        return {
            "reply": "You're welcome! I can help with tasks, room booking, meetings, and availability.",
            "tool_calls": [],
        }

    if re.search(r"\b(my tasks|show my tasks|what are my tasks)\b", text):
        tasks = get_my_tasks(db, user)
        return {"reply": format_my_tasks(tasks), "tool_calls": [{"tool": "get_my_tasks"}]}

    if re.search(r"\b(team status|my team|show team status|overdue)\b", text):
        if user.role not in (UserRole.MANAGER, UserRole.ADMIN):
            return {"reply": "Only manager/admin can view team status.", "tool_calls": []}
        return {"reply": format_team_status(db, user), "tool_calls": [{"tool": "get_team_status"}]}

    if re.search(r"\b(list rooms|meeting rooms|all rooms)\b", text):
        result = list_rooms(db)
        rooms = result.get("rooms", [])
        if not rooms:
            return {"reply": "No rooms found.", "tool_calls": []}
        lines = ["Available rooms:"] + [
            f"- {r['name']} (capacity {r['capacity']}, type: {r['type']})" for r in rooms
        ]
        return {"reply": "\n".join(lines), "tool_calls": [{"tool": "list_rooms"}]}

    book_match = re.search(
        r"\bbook\s+(?:room\s+)?(.+?)\s+for\s+(.+)$",
        text,
        re.IGNORECASE,
    )
    if not book_match:
        book_match = re.search(
            r"\bbook\s+(?:room\s+)?(.+?)\s+(today|tomorrow)\s+(.+)$",
            text,
            re.IGNORECASE,
        )
    if book_match:
        if len(book_match.groups()) == 2:
            room_name = book_match.group(1).strip()
            time_part = book_match.group(2).strip()
            date = _TODAY_STR
        else:
            room_name = book_match.group(1).strip()
            date = resolve_date(book_match.group(2).strip())
            time_part = book_match.group(3).strip()
        start_hour, end_hour = parse_hour_range(time_part)
        start_time = datetime.fromisoformat(f"{date}T{start_hour:02d}:00:00")
        end_time = datetime.fromisoformat(f"{date}T{end_hour:02d}:00:00")
        result = book_room(db, user.name, room_name, "Meeting", start_time, end_time)
        if result.get("success"):
            return {
                "reply": (
                    f"Booked {result.get('room')} from {start_time.strftime('%I:%M %p')} "
                    f"to {end_time.strftime('%I:%M %p')} on {date}."
                ),
                "tool_calls": [{"tool": "book_room", "result": result}],
            }
        return {
            "reply": result.get("error", "Booking failed.") + (
                f" Conflicts: {result.get('conflicts')}" if result.get("conflicts") else ""
            ),
            "tool_calls": [{"tool": "book_room", "result": result}],
        }

    assign_match = re.search(
        r"assign task[:\s]+(.+?)\s+to\s+(.+?)\s+due\s+(.+)$",
        message.strip(),
        re.IGNORECASE,
    )
    if assign_match:
        if user.role not in (UserRole.MANAGER, UserRole.ADMIN):
            return {"reply": "Only manager/admin can assign tasks.", "tool_calls": []}
        title = assign_match.group(1).strip().strip('"')
        assignee_name = assign_match.group(2).strip().strip('"')
        due_raw = assign_match.group(3).strip()
        assignee = find_person_by_name(db, assignee_name)
        if not assignee:
            return {"reply": f"Could not find assignee '{assignee_name}'.", "tool_calls": []}
        try:
            due_date = parse_due_date(due_raw)
            task = assign_task_to_user(
                db,
                user,
                assignee,
                title,
                title,
                "high" if "high" in text else "medium",
                due_date,
            )
        except PermissionError as e:
            return {"reply": str(e), "tool_calls": []}
        except ValueError:
            return {
                "reply": f"Could not understand due date '{due_raw}'. Use tomorrow or YYYY-MM-DD.",
                "tool_calls": [],
            }
        return {
            "reply": f"Task assigned successfully to {assignee.name} (task id {task.id}).",
            "tool_calls": [{"tool": "assign_task", "task_id": task.id}],
        }

    avail_words = r"(available|free|coming|in\s+office|around)"

    avail_match = re.search(
        rf"(?:is\s+)?(.+?)\s+{avail_words}\s+(.+)$",
        text,
        re.IGNORECASE,
    )
    if avail_match:
        return _availability_reply(db, user, avail_match.group(1), avail_match.group(3))

    avail_no_date = re.search(
        rf"(?:is\s+)?(.+?)\s+{avail_words}$",
        text,
        re.IGNORECASE,
    )
    if avail_no_date:
        return _availability_reply(db, user, avail_no_date.group(1), "today")

    return None
