from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, get_db
from app.paths import STATIC_DIR
from app.routers import auth, chat, dashboard, leaves, meetings, pages, tasks, users
from app.seed import migrate_demo_passwords, seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_database(db)
        migrate_demo_passwords(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Office Copilot API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(meetings.router)
app.include_router(tasks.router)
app.include_router(leaves.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
