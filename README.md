# GYM — Gain Your Muscles

AI-powered fitness platform: personalized workouts with progressive overload, nutrition planning, blog, community FAQ, and admin panel.

## Stack
- **Frontend:** Next.js 15 (App Router) · TypeScript · Tailwind · Framer Motion · Lucide
- **Backend:** FastAPI (async) · Pydantic v2 · SQLAlchemy 2 · Alembic · JWT
- **DB:** PostgreSQL 16 (JSONB)
- **Infra:** Docker Compose · Caddy

## Quick start

```bash
cp .env.example .env
docker compose up --build -d
```

- App: `http://localhost`
- API: `http://localhost/api/docs`
- Admin: `http://localhost/admin` (login with `ADMIN_EMAIL` / `ADMIN_PASSWORD`)

**Full build & run guide (Docker, macOS/Linux, Windows, troubleshooting):** see [`BUILD.md`](./BUILD.md).

## Architecture

```
routes  ─▶  services  ─▶  repositories  ─▶  models (SQLAlchemy)
             ▲
             └── schemas (Pydantic v2)
```

Feature-based frontend: `app/` routes, `components/` primitives + feature UIs, `features/` per-domain API + types, `lib/` shared infra.

## Local dev (without Docker)

```bash
# backend
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://gym:gym@localhost:5432/gym alembic upgrade head
python -m app.data.seed_exercises
uvicorn app.main:app --reload

# frontend
cd frontend
npm i && npm run dev
```
