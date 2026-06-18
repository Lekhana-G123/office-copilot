from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _normalize_database_url(url: str) -> str:
    """Render/Neon sometimes use postgres:// — SQLAlchemy needs postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


_db_url = _normalize_database_url(settings.database_url)

_connect_args: dict = {}
_engine_kwargs: dict = {"pool_pre_ping": True}

if _db_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
else:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 10

engine = create_engine(_db_url, connect_args=_connect_args, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
