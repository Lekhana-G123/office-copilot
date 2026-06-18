from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import (
    Announcement,
    Leave,
    LeaveStatus,
    LeaveType,
    Meeting,
    MeetingAttendee,
    MeetingStatus,
    Room,
    Task,
    TaskStatus,
    User,
    UserRole,
)


def seed_database(db: Session) -> None:
    if db.query(User).first():
        return

    user_specs = [
        # Existing demo logins
        ("HR Admin", "admin@office.com", "admin123", UserRole.ADMIN, "HR", False),
        ("Director Kumar", "director@office.com", "welcome123", UserRole.EXECUTIVE, "Leadership", True),
        ("Priya (EA)", "ea@office.com", "ea123", UserRole.EA, "Leadership", False),
        ("Team Lead", "manager@office.com", "mgr123", UserRole.MANAGER, "Engineering", False),
        ("You (Intern)", "intern@office.com", "intern123", UserRole.EMPLOYEE, "Engineering", False),
        # Admin / HR
        ("Nisha HR", "nisha.hr@office.com", "welcome123", UserRole.ADMIN, "HR", False),
        # Executives
        ("Ananya Rao (Director)", "ananya.director@office.com", "welcome123", UserRole.EXECUTIVE, "Leadership", True),
        ("Vikram Shah (Director)", "vikram.director@office.com", "welcome123", UserRole.EXECUTIVE, "Leadership", True),
        # EA
        ("Ritu (EA)", "ritu.ea@office.com", "welcome123", UserRole.EA, "Leadership", False),
        # Managers / TLs
        ("Meera TL", "meera.manager@office.com", "welcome123", UserRole.MANAGER, "Engineering", False),
        ("Arjun TL", "arjun.manager@office.com", "welcome123", UserRole.MANAGER, "Engineering", False),
        ("Pooja Manager", "pooja.manager@office.com", "welcome123", UserRole.MANAGER, "Operations", False),
        ("Rahul Manager", "rahul.manager@office.com", "welcome123", UserRole.MANAGER, "Sales", False),
        # Employees / interns (role=EMPLOYEE)
        ("Aditi Intern", "aditi.intern@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
        ("Neha Intern", "neha.intern@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
        ("Karan Intern", "karan.intern@office.com", "welcome123", UserRole.EMPLOYEE, "Data", False),
        ("Isha Sharma", "isha.sharma@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
        ("Rohit Verma", "rohit.verma@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
        ("Sneha Patil", "sneha.patil@office.com", "welcome123", UserRole.EMPLOYEE, "Data", False),
        ("Kabir Malhotra", "kabir.malhotra@office.com", "welcome123", UserRole.EMPLOYEE, "Data", False),
        ("Divya Menon", "divya.menon@office.com", "welcome123", UserRole.EMPLOYEE, "Design", False),
        ("Aman Gupta", "aman.gupta@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
        ("Shreya Nair", "shreya.nair@office.com", "welcome123", UserRole.EMPLOYEE, "Operations", False),
        ("Nitin Batra", "nitin.batra@office.com", "welcome123", UserRole.EMPLOYEE, "Operations", False),
        ("Tanya Joshi", "tanya.joshi@office.com", "welcome123", UserRole.EMPLOYEE, "Sales", False),
        ("Sahil Arora", "sahil.arora@office.com", "welcome123", UserRole.EMPLOYEE, "Sales", False),
        ("Rhea Kapoor", "rhea.kapoor@office.com", "welcome123", UserRole.EMPLOYEE, "HR", False),
        ("Yash Kulkarni", "yash.kulkarni@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
        ("Manvi Jain", "manvi.jain@office.com", "welcome123", UserRole.EMPLOYEE, "Data", False),
        ("Pranav Iyer", "pranav.iyer@office.com", "welcome123", UserRole.EMPLOYEE, "Engineering", False),
    ]

    users = []
    for name, email, password, role, department, bookable_exec in user_specs:
        users.append(
            User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role,
                department=department,
                is_bookable_executive=bookable_exec,
            )
        )

    db.add_all(users)
    db.flush()

    users_by_email = {u.email: u for u in users}
    users_by_email["director@office.com"].delegate_user_id = users_by_email["ea@office.com"].id
    users_by_email["ananya.director@office.com"].delegate_user_id = users_by_email["ea@office.com"].id
    users_by_email["vikram.director@office.com"].delegate_user_id = users_by_email["ritu.ea@office.com"].id
    users_by_email["intern@office.com"].manager_id = users_by_email["manager@office.com"].id
    users_by_email["aditi.intern@office.com"].manager_id = users_by_email["meera.manager@office.com"].id
    users_by_email["neha.intern@office.com"].manager_id = users_by_email["meera.manager@office.com"].id
    users_by_email["karan.intern@office.com"].manager_id = users_by_email["arjun.manager@office.com"].id
    users_by_email["isha.sharma@office.com"].manager_id = users_by_email["meera.manager@office.com"].id
    users_by_email["rohit.verma@office.com"].manager_id = users_by_email["manager@office.com"].id
    users_by_email["sneha.patil@office.com"].manager_id = users_by_email["arjun.manager@office.com"].id
    users_by_email["kabir.malhotra@office.com"].manager_id = users_by_email["arjun.manager@office.com"].id
    users_by_email["divya.menon@office.com"].manager_id = users_by_email["meera.manager@office.com"].id
    users_by_email["aman.gupta@office.com"].manager_id = users_by_email["manager@office.com"].id
    users_by_email["shreya.nair@office.com"].manager_id = users_by_email["pooja.manager@office.com"].id
    users_by_email["nitin.batra@office.com"].manager_id = users_by_email["pooja.manager@office.com"].id
    users_by_email["tanya.joshi@office.com"].manager_id = users_by_email["rahul.manager@office.com"].id
    users_by_email["sahil.arora@office.com"].manager_id = users_by_email["rahul.manager@office.com"].id
    users_by_email["rhea.kapoor@office.com"].manager_id = users_by_email["admin@office.com"].id
    users_by_email["yash.kulkarni@office.com"].manager_id = users_by_email["manager@office.com"].id
    users_by_email["manvi.jain@office.com"].manager_id = users_by_email["arjun.manager@office.com"].id
    users_by_email["pranav.iyer@office.com"].manager_id = users_by_email["manager@office.com"].id

    db.add_all([
        Room(name="Conference Room A", capacity=8, room_type="meeting"),
        Room(name="Conference Room B", capacity=4, room_type="meeting"),
        Room(name="Conference Room C", capacity=12, room_type="meeting"),
        Room(name="Board Room", capacity=16, room_type="meeting"),
        Room(name="Hot Desk 12", capacity=1, room_type="desk"),
        Room(name="Hot Desk 21", capacity=1, room_type="desk"),
    ])
    db.flush()

    db.add(Announcement(
        title="Welcome to Office Copilot",
        body="Use the assistant to check director availability and book rooms.",
        posted_by_id=users_by_email["admin@office.com"].id,
    ))

    db.add_all([
        Task(
            title="Set up dev environment",
            description="Clone repo and run seed.",
            assignee_id=users_by_email["intern@office.com"].id,
            created_by_id=users_by_email["manager@office.com"].id,
            status=TaskStatus.OPEN,
            priority="high",
            due_date=datetime.utcnow() + timedelta(days=3),
        ),
        Task(
            title="Prepare Q2 team status report",
            description="Consolidate updates from engineering and data teams.",
            assignee_id=users_by_email["isha.sharma@office.com"].id,
            created_by_id=users_by_email["meera.manager@office.com"].id,
            status=TaskStatus.IN_PROGRESS,
            priority="medium",
            due_date=datetime.utcnow() + timedelta(days=2),
        ),
        Task(
            title="Sales pipeline cleanup",
            description="Update stale opportunities and follow-up dates.",
            assignee_id=users_by_email["tanya.joshi@office.com"].id,
            created_by_id=users_by_email["rahul.manager@office.com"].id,
            status=TaskStatus.OPEN,
            priority="high",
            due_date=datetime.utcnow() + timedelta(days=1),
        ),
    ])

    tomorrow = datetime.utcnow().replace(hour=14, minute=0, second=0, microsecond=0) + timedelta(days=1)
    meeting = Meeting(
        title="Board prep",
        organizer_id=users_by_email["ea@office.com"].id,
        start_time=tomorrow,
        end_time=tomorrow + timedelta(hours=1),
        status=MeetingStatus.CONFIRMED,
    )
    db.add(meeting)
    db.flush()

    db.add(MeetingAttendee(meeting_id=meeting.id, user_id=users_by_email["director@office.com"].id, is_required=True))
    db.add(MeetingAttendee(meeting_id=meeting.id, user_id=users_by_email["ea@office.com"].id, is_required=True))

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    db.add_all([
        Leave(
            user_id=users_by_email["aditi.intern@office.com"].id,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            leave_type=LeaveType.LEAVE,
            status=LeaveStatus.APPROVED,
            reason="Medical leave",
            approved_by=users_by_email["meera.manager@office.com"].id,
        ),
        Leave(
            user_id=users_by_email["tanya.joshi@office.com"].id,
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=3),
            leave_type=LeaveType.LEAVE,
            status=LeaveStatus.PENDING,
            reason="Personal work",
            approved_by=None,
        ),
        Leave(
            user_id=users_by_email["intern@office.com"].id,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=5),
            leave_type=LeaveType.LEAVE,
            status=LeaveStatus.APPROVED,
            reason="Exam leave",
            approved_by=users_by_email["manager@office.com"].id,
        ),
    ])

    db.commit()


def migrate_demo_passwords(db: Session) -> None:
    """Keep demo logins working on existing databases."""
    director = db.query(User).filter(User.email == "director@office.com").first()
    if director:
        director.password_hash = hash_password("welcome123")
        db.commit()