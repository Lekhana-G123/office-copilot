# Office Copilot

A workplace assistant for tasks, meetings, room booking, leave, and AI chat — with role-based access (employee, manager, EA, admin, executive).

**Live app:** https://office-copilot.onrender.com/dashboard

---

## What it does

- **Dashboard** — tasks, meetings, rooms, leave, team view, approvals
- **AI chat** — ask in plain English ("show my tasks", "book room A", "is director available tomorrow")
- **Roles** — intern, manager, EA, admin, director each see different views
- **Approvals** — EA approves meeting requests; managers approve leave

---

## Tech stack

### Application

| Part | Technology |
|------|------------|
| Backend API | Python, FastAPI, SQLAlchemy |
| Auth | JWT + bcrypt |
| AI chat | Groq API (Llama) + quick commands |
| Frontend | HTML / CSS / JavaScript |

### Local development

| Part | Technology |
|------|------------|
| Database | SQLite (`data/office.db`) |
| Server | Uvicorn on `http://127.0.0.1:8000` |

### Production (live)

| Part | Service | Purpose |
|------|---------|---------|
| Code | GitHub | Source control + deploy |
| App hosting | Render | Runs FastAPI (API + website) |
| Database | Neon | PostgreSQL (storage only — not an API) |
| AI | Groq | Chat responses |

**Production flow:**

GitHub → Render (FastAPI API) → Neon (PostgreSQL)
              ↓
         Groq (AI chat)

- Neon gives a database connection string only.
- API (`/login`, `/chat`, `/dashboard/me`, etc.) comes from FastAPI on Render.

---

## Run locally

1. Python 3.12 + Git
2. `python -m venv venv`
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` — set `GROQ_API_KEY`, `SECRET_KEY`
5. Run `start.bat` or: `uvicorn app.main:app --reload`
6. Open http://127.0.0.1:8000/dashboard

---

## Demo logins

| Role | Email | Password |
|------|--------|----------|
| Intern | intern@office.com | intern123 |
| Manager | manager@office.com | mgr123 |
| EA | ea@office.com | ea123 |
| Admin | admin@office.com | admin123 |
| Director | director@office.com | welcome123 |

---

## Production deploy (Render + Neon)

Environment variables on Render:

| Variable | Value |
|----------|--------|
| PYTHON_VERSION | 3.12.7 |
| DATABASE_URL | Neon postgresql://... |
| SECRET_KEY | Random string |
| GROQ_API_KEY | From groq.com |
| RUN_SEED | true |
| CORS_ORIGINS | https://office-copilot.onrender.com |

Build: `pip install -r requirements.txt`  
Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

---

## Repository

https://github.com/Lekhana-G123/office-copilot
