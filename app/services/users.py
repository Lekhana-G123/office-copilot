from sqlalchemy.orm import Session

from app.models import User


def find_person_by_name(db: Session, name: str) -> User | None:
    """Find user by partial name match (case-insensitive)."""
    name_lower = name.lower().strip()
    users = db.query(User).all()
    for user in users:
        if name_lower in user.name.lower():
            return user
    return None


def get_team_member_ids(db: Session, manager_id: int) -> list[int]:
    members = db.query(User).filter(User.manager_id == manager_id).all()
    return [m.id for m in members]
