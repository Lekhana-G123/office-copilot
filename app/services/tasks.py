from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Task, TaskStatus, User, UserRole
from app.services.users import find_person_by_name
from app.utils.dates import parse_due_date


def get_my_tasks(db: Session, user: User) -> list[Task]:
    return db.query(Task).filter(Task.assignee_id == user.id).all()


def format_my_tasks(tasks: list[Task]) -> str:
    if not tasks:
        return "You have no tasks assigned."
    lines = ["Your tasks:"]
    for t in tasks:
        due = t.due_date.isoformat() if t.due_date else "no due date"
        lines.append(f"- [{t.status.value}] {t.title} (priority: {t.priority}, due: {due})")
    return "\n".join(lines)


def get_team_tasks(db: Session, manager: User) -> tuple[list[User], list[Task], list[Task]]:
    members = db.query(User).filter(User.manager_id == manager.id).all()
    member_ids = [m.id for m in members]
    team_tasks = (
        db.query(Task).filter(Task.assignee_id.in_(member_ids)).all() if member_ids else []
    )
    overdue = [
        t for t in team_tasks
        if t.due_date and t.due_date < datetime.utcnow() and t.status != TaskStatus.DONE
    ]
    return members, team_tasks, overdue


def format_team_status(db: Session, manager: User) -> str:
    members, team_tasks, overdue = get_team_tasks(db, manager)
    lines = [
        f"Team size: {len(members)}",
        f"Open: {len([t for t in team_tasks if t.status == TaskStatus.OPEN])} | "
        f"In progress: {len([t for t in team_tasks if t.status == TaskStatus.IN_PROGRESS])} | "
        f"Done: {len([t for t in team_tasks if t.status == TaskStatus.DONE])}",
    ]
    if overdue:
        lines.append("Overdue tasks:")
        for t in overdue:
            lines.append(f"- {t.title} (task id {t.id})")
    else:
        lines.append("No overdue tasks in your team.")
    return "\n".join(lines)


def get_team_status_dict(db: Session, manager: User) -> dict:
    if manager.role not in (UserRole.MANAGER, UserRole.ADMIN):
        return {"success": False, "error": "Only manager/admin can view team status"}
    members, team_tasks, overdue = get_team_tasks(db, manager)
    return {
        "success": True,
        "team_size": len(members),
        "open": len([t for t in team_tasks if t.status == TaskStatus.OPEN]),
        "in_progress": len([t for t in team_tasks if t.status == TaskStatus.IN_PROGRESS]),
        "done": len([t for t in team_tasks if t.status == TaskStatus.DONE]),
        "overdue_tasks": [
            {"id": t.id, "title": t.title, "assignee_id": t.assignee_id}
            for t in overdue
        ],
    }


def assign_task_to_user(
    db: Session,
    creator: User,
    assignee: User,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: datetime | None = None,
) -> Task:
    if creator.role not in (UserRole.MANAGER, UserRole.ADMIN):
        raise PermissionError("Only manager/admin can assign tasks")
    if creator.role == UserRole.MANAGER and assignee.manager_id != creator.id:
        raise PermissionError("Managers can assign only to team members")

    task = Task(
        title=title,
        description=description,
        assignee_id=assignee.id,
        created_by_id=creator.id,
        status=TaskStatus.OPEN,
        priority=priority,
        due_date=due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def assign_task_by_names(
    db: Session,
    manager_name: str,
    assignee_name: str,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date_str: str = "",
) -> dict:
    manager = find_person_by_name(db, manager_name)
    assignee = find_person_by_name(db, assignee_name)
    if not manager or not assignee:
        return {"success": False, "error": "Manager or assignee not found"}
    try:
        due_date = parse_due_date(due_date_str) if due_date_str else None
        task = assign_task_to_user(
            db, manager, assignee, title, description, priority, due_date
        )
    except PermissionError as e:
        return {"success": False, "error": str(e)}
    return {"success": True, "task_id": task.id, "assignee": assignee.name}
