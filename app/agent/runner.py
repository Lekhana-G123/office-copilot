from sqlalchemy.orm import Session

from app.services.availability import (
    check_person_availability,
    check_person_availability_for_viewer,
)
from app.services.meetings import create_meeting_request, draft_meeting_email
from app.services.rooms import book_room, check_room_availability, list_rooms
from app.services.tasks import assign_task_by_names, get_my_tasks, get_team_status_dict
from app.services.users import find_person_by_name
from app.utils.dates import parse_time_range


def run_tool(db: Session, name: str, args: dict) -> dict:
    if name == "check_availability":
        viewer = find_person_by_name(db, args.get("requester_name", ""))
        start_hour = args.get("start_hour", 14)
        end_hour = args.get("end_hour", 15)
        start_time, end_time = parse_time_range(args["date"], start_hour, end_hour)
        if viewer:
            return check_person_availability_for_viewer(
                db, viewer, args["person_name"], start_time, end_time
            )
        return check_person_availability(db, args["person_name"], start_time, end_time)

    if name == "create_meeting_request":
        start_hour = args.get("start_hour", 14)
        end_hour = args.get("end_hour", 15)
        start_time, end_time = parse_time_range(args["date"], start_hour, end_hour)
        return create_meeting_request(
            db,
            args["requester_name"],
            args["target_person_name"],
            args["reason"],
            start_time,
            end_time,
        )

    if name == "draft_meeting_email":
        viewer = find_person_by_name(db, args.get("requester_name", ""))
        start_hour = args.get("start_hour", 14)
        end_hour = args.get("end_hour", 15)
        start_time, end_time = parse_time_range(args["date"], start_hour, end_hour)
        availability = (
            check_person_availability_for_viewer(
                db, viewer, args["target_person_name"], start_time, end_time
            )
            if viewer
            else check_person_availability(
                db, args["target_person_name"], start_time, end_time
            )
        )
        return draft_meeting_email(
            args["requester_name"],
            args["target_person_name"],
            args["reason"],
            start_time,
            end_time,
            availability["available"],
            availability.get("conflicts"),
        )

    if name == "find_person":
        person = find_person_by_name(db, args["name"])
        if not person:
            return {"found": False, "name": args["name"]}
        return {
            "found": True,
            "name": person.name,
            "email": person.email,
            "role": person.role.value,
            "department": person.department,
            "is_executive": person.is_bookable_executive,
        }

    if name == "list_rooms":
        return list_rooms(db)

    if name == "check_room_availability":
        start_hour = args.get("start_hour", 10)
        end_hour = args.get("end_hour", 11)
        start_time, end_time = parse_time_range(args["date"], start_hour, end_hour)
        return check_room_availability(db, args["room_name"], start_time, end_time)

    if name == "book_room":
        start_hour = args.get("start_hour", 10)
        end_hour = args.get("end_hour", 11)
        start_time, end_time = parse_time_range(args["date"], start_hour, end_hour)
        return book_room(
            db,
            args["booker_name"],
            args["room_name"],
            args["title"],
            start_time,
            end_time,
        )

    if name == "get_my_tasks":
        requester = find_person_by_name(db, args["requester_name"])
        if not requester:
            return {"success": False, "error": "User not found"}
        rows = get_my_tasks(db, requester)
        return {
            "success": True,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                }
                for t in rows
            ],
        }

    if name == "get_team_status":
        manager = find_person_by_name(db, args["manager_name"])
        if not manager:
            return {"success": False, "error": "Manager not found"}
        return get_team_status_dict(db, manager)

    if name == "assign_task":
        return assign_task_by_names(
            db,
            args["manager_name"],
            args["assignee_name"],
            args["title"],
            args.get("description", ""),
            args.get("priority", "medium"),
            args.get("due_date", ""),
        )

    return {"error": f"Unknown tool: {name}"}
