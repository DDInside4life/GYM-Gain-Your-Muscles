# GYM — Build & Run Guide

Complete, step-by-step instructions to build and run the **GYM** fullstack app
(Next.js 15 + FastAPI + PostgreSQL 16). Three supported paths:

1. **Docker Compose** — one-command production-like stack (recommended)
2. **Local dev (Linux / macOS)** — hot reload, no Docker for app code
3. **Local dev (Windows / PowerShell)** — same, adapted for Windows

---

## 0. Prerequisites

| Tool                                  | Version  | Notes                                                     |
| ------------------------------------- | -------- | --------------------------------------------------------- |
| Git                                   | any      |                                                           |
| Docker Desktop (for path 1)           | 24+      | Includes Docker Compose v2                                |
| Python                                | 3.12     | Only for local dev                                        |
| Node.js                               | 20 LTS   | Only for local dev                                        |
| PostgreSQL                            | 16+      | Only if you run DB locally (not via Docker)               |

Clone:

```bash
git clone <repo-url> gym
cd gym
cp .env.example .env         # macOS / Linux
# Windows PowerShell:
Copy-Item .env.example .env
```

Open `.env` and set **at minimum**:

```dotenv
ENVIRONMENT=development
POSTGRES_USER=gym
POSTGRES_PASSWORD=change-me-in-production
POSTGRES_DB=gym
SECRET_KEY=dev-only-change-me-to-32+chars-random
ADMIN_EMAIL=admin@example.com          # MUST be a real TLD (.local is rejected by EmailStr)
ADMIN_PASSWORD=change-me-in-production
NEXT_PUBLIC_API_URL=/api               # same-origin via Caddy proxy
SITE_ADDRESS=:80                       # or your domain, e.g. gym.example.com
RATE_LIMIT_LOGIN=20/minute
SEED_EXERCISES=1
```

> **Important:** `admin@gym.local` **will fail** Pydantic validation —
> `email-validator` rejects the `.local` TLD. Always use a real TLD.

---

## 1. Path A — Docker Compose (recommended)

### 1.1 Launch

```bash
docker compose up --build -d
docker compose logs -f backend
```

What you get:
- Caddy on **:80** (and :443) → reverse-proxies `/api/*` to backend, everything else to Next.js
- Backend on internal `backend:8000`
- Frontend on internal `frontend:3000`
- Postgres internal only (no host port exposed)
- On first backend boot: Alembic migrations run, admin user is created, exercises are seeded if `SEED_EXERCISES=1`.

### 1.2 Verify

```bash
curl http://localhost/api/health
curl http://localhost/api/exercises?limit=1
```

Open:
- **App:** http://localhost
- **API docs:** http://localhost/api/docs
- **Admin panel:** http://localhost/admin (login with `ADMIN_EMAIL` / `ADMIN_PASSWORD`)

### 1.3 Common operations

```bash
# Stop
docker compose down

# Wipe DB and start fresh (destroys data)
docker compose down -v && docker compose up --build -d

# Run a one-off Alembic command
docker compose exec backend alembic upgrade head

# Re-seed exercises
docker compose exec backend python -m app.data.seed_exercises

# Shell into DB
docker compose exec db psql -U gym -d gym
```

---

## 2. Path B — Local dev (Linux / macOS)

### 2.1 Start PostgreSQL (Docker is simplest)

```bash
docker run -d --name gym-db \
  -e POSTGRES_USER=gym -e POSTGRES_PASSWORD=gym -e POSTGRES_DB=gym \
  -p 5432:5432 postgres:16-alpine
```

### 2.2 Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

export DATABASE_URL="postgresql+asyncpg://gym:gym@localhost:5432/gym"
export ENVIRONMENT=development
export SECRET_KEY="dev-only-change-me"
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="change-me-in-production"

alembic upgrade head
python -m app.data.seed_exercises
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify:

```bash
curl http://127.0.0.1:8000/api/health
open http://127.0.0.1:8000/api/docs
```

### 2.3 Frontend

```bash
cd frontend
npm ci
# Point the browser directly at the backend (no Caddy in local dev)
export NEXT_PUBLIC_API_URL="http://127.0.0.1:8000/api"
npm run dev
```

Open http://127.0.0.1:3000 and register / log in.

---

## 3. Path C — Local dev (Windows / PowerShell)

> All commands verified on Windows 10 PowerShell 5.1.

### 3.1 Start PostgreSQL

Easiest with Docker Desktop:

```powershell
docker run -d --name gym-db `
  -e POSTGRES_USER=gym -e POSTGRES_PASSWORD=gym -e POSTGRES_DB=gym `
  -p 5432:5432 postgres:16-alpine
```

Or use a local Postgres install — then add its `bin` to `PATH` so `psql` works:

```powershell
$env:Path = "C:\Program Files\PostgreSQL\18\bin;$env:Path"
```

### 3.2 Backend

```powershell
cd C:\GYM\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt

$env:DATABASE_URL    = "postgresql+asyncpg://gym:gym@localhost:5432/gym"
$env:ENVIRONMENT     = "development"
$env:SECRET_KEY      = "dev-only-change-me"
$env:ADMIN_EMAIL     = "admin@example.com"
$env:ADMIN_PASSWORD  = "change-me-in-production"

alembic upgrade head
python -m app.data.seed_exercises
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Smoke test in another terminal:

```powershell
curl.exe http://127.0.0.1:8000/api/health
curl.exe "http://127.0.0.1:8000/api/exercises?limit=1"
```

> **Register / login from PowerShell** — always send JSON from a file, not an
> inline string, to avoid PowerShell stripping the quotes:
>
> ```powershell
> '{"email":"admin@example.com","password":"change-me-in-production"}' |
>   Out-File "$env:TEMP\login.json" -Encoding ASCII -NoNewline
> curl.exe -s -X POST http://127.0.0.1:8000/api/auth/login `
>   -H "content-type: application/json" `
>   --data-binary "@$env:TEMP\login.json"
> ```

### 3.3 Frontend

```powershell
cd C:\GYM\frontend
npm ci
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000/api"
npm run dev
```

Open http://127.0.0.1:3000.

---

## 4. Project structure

```
GYM/
├── backend/                     # FastAPI app
│   ├── app/
│   │   ├── core/                # config, db, security, deps, limiter, exceptions
│   │   ├── models/              # SQLAlchemy 2 ORM
│   │   ├── schemas/             # Pydantic v2
│   │   ├── repositories/        # DB access
│   │   ├── services/            # business rules (auth, blog, forum, nutrition,
│   │   │   └── workout/         # workout engine: rules, splits, generator, progression
│   │   ├── routes/              # HTTP endpoints
│   │   ├── data/seed_exercises  # initial exercises
│   │   └── main.py              # app factory + lifespan (migrations, admin, seed)
│   ├── alembic/                 # migrations
│   ├── Dockerfile               # multi-stage, non-root, tini
│   └── requirements.txt
├── frontend/                    # Next.js 15 App Router
│   └── src/{app,components,features,lib}
├── infra/
│   └── Caddyfile                # reverse proxy, TLS, security headers
├── docker-compose.yml
├── .env.example
└── README.md
```

Architecture:

```
route  ─▶  service  ─▶  repository  ─▶  model
              ▲
              └── schema (Pydantic v2)
```

---

## 5. Reset procedures

### Nuke DB (Docker)

```bash
docker compose down -v
docker compose up --build -d
```

### Nuke DB (local Postgres)

```bash
psql -U gym -d postgres -c "DROP DATABASE gym;"
psql -U gym -d postgres -c "CREATE DATABASE gym;"
# then re-run alembic upgrade head + seed
```

Or the nuclear option that keeps the DB but clears all tables & enums:

```sql
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

### Recreate admin (when you change `ADMIN_EMAIL`)

```sql
DELETE FROM users WHERE email='old-admin@example.com';
```

Then restart the backend — the `lifespan` hook recreates the admin from env vars.

---

## 6. Troubleshooting (real issues we hit)

| Symptom                                                                                   | Cause                                                                                            | Fix                                                                                                                          |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `DuplicateObjectError: type "user_sex" already exists` during `alembic upgrade head`      | Previous migration failed half-way and left enums in the DB.                                     | `DROP SCHEMA public CASCADE; CREATE SCHEMA public;` then re-run `alembic upgrade head`.                                      |
| `UndefinedTableError: relation "exercises" does not exist` during seed                    | Migrations never completed (see above).                                                          | Fix migration first, then `python -m app.data.seed_exercises`.                                                               |
| `AssertionError: Status code 204 must not have a response body`                           | FastAPI 0.115 infers a response model from `-> None`.                                            | Already fixed in code (`response_class=Response`, explicit `Response(status_code=204)`). Pull latest.                        |
| `POST /api/auth/login` → **422** `{loc:["query","payload"], msg:"Field required"}`        | `slowapi` decorator + `from __future__ import annotations` confused FastAPI signature parsing.   | Already fixed: `payload: Annotated[LoginInput, Body()]`. Make sure you're running the latest `backend/app/routes/auth.py`.   |
| `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`             | Stale `uvicorn --reload` process still holding the port.                                         | `netstat -ano \| findstr :8000` → `Stop-Process -Id <PID> -Force` (kill the **worker**, the reloader parent will then exit). |
| `admin@gym.local` rejected with "The part after the @-sign is not valid (reserved TLD)"   | `email-validator` rejects `.local`.                                                              | Use a real TLD: `ADMIN_EMAIL=admin@example.com`, delete the old row, restart.                                                |
| `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`                     | Broken venv / mismatched Python ABI.                                                             | Recreate the venv: delete `.venv` → `py -3.12 -m venv .venv` → reinstall.                                                    |
| PowerShell `curl` sends `{email:...}` instead of `{"email":...}` and server returns 422   | PowerShell strips the inner double-quotes from inline JSON.                                      | Write JSON to a file and use `curl.exe --data-binary "@file.json"`.                                                          |
| Frontend shows login but network tab hits `localhost:8000` (CORS fail) in Docker          | `NEXT_PUBLIC_API_URL` not `/api`.                                                                | In Docker set `NEXT_PUBLIC_API_URL=/api` (Caddy proxies). Only in local dev set full URL.                                    |

---

## 7. Quick "smoke" script

Run after any change to verify the stack end-to-end:

```bash
BASE=http://localhost       # Docker
# BASE=http://127.0.0.1:8000  # local dev

curl -sf $BASE/api/health
curl -sf "$BASE/api/exercises?limit=1"

# register
curl -sf -X POST $BASE/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"u1@example.com","password":"Password123!","full_name":"U One"}'

# login
TOK=$(curl -s -X POST $BASE/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"u1@example.com","password":"Password123!"}' | jq -r .access_token)

curl -sf $BASE/api/auth/me -H "authorization: Bearer $TOK"
```

If every line prints valid JSON without a non-2xx status, the stack is healthy.

---

## 8. Production checklist

Before deploying beyond `ENVIRONMENT=development`:

- [ ] `SECRET_KEY` is 32+ random chars (not starting with `dev-`).
- [ ] Strong `POSTGRES_PASSWORD` and `ADMIN_PASSWORD`.
- [ ] `SITE_ADDRESS=your.domain` in `.env` so Caddy issues a real TLS cert.
- [ ] `SEED_EXERCISES=0` after the first successful boot.
- [ ] DB backups scheduled (`pg_dump`).
- [ ] `docker compose up -d` runs as a service (systemd / task scheduler).
- [ ] Logs shipped somewhere (`docker compose logs` is not a backup).
