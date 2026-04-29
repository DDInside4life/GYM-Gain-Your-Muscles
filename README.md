# GYM — Gain Your Muscles

Production fitness web app: deterministic template-based workout planning,
manual nutrition tracking with a calorie calculator, user progress, and
community content (blog + FAQ). Russian UI.

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

## Workout module — design rules

Workout generation is **deterministic and questionnaire-driven**. There is a
single materialization path: every endpoint flows through `WorkoutGenerator`.
Seeded templates are kept read-only as inspiration (`GET /workouts/predefined`,
`GET /templates`); they never bypass the generator.

1. The user answers a single questionnaire (sex, age, height, weight,
   experience, goal, location, equipment, injuries, days/week, available days,
   session duration, training structure, periodization, cycle length, priority
   exercises). All 17 fields influence the output.
2. `WorkoutGenerator.generate_from_context` orchestrates pure modules:
   `filtering` → `volume` budget → `splits` → `recovery` placement →
   `load_progression` (sets/reps/weight/RIR/RPE) → persistence.
3. **Test week = week 1.** For exercises with `suitable_for_test=True` the
   generator emits one working set at `reps_max+2` with RIR≈2 and a Russian
   `test_instruction`; the starter weight is `0.6 × e1RM_prev` (or
   `starter_weight(archetype, experience, goal)` if no prior e1RM exists). All
   periodization week-modifiers are suppressed during the test week.
4. **Working weeks (2..N) use the auto-weight formula:**
   `weight = round_to_plate(min(e1RM × TARGET_PERCENT[goal][week_kind],
   volume_cap))` with safety clamp by archetype/experience. The percent table
   lives in `services/workout/load_progression.py::TARGET_PERCENT` and is
   shaped by goal (strength/hypertrophy/fat-loss/endurance/general).
5. **Periodization** styles (`linear`, `dup`, `block`, `emergent`) scale
   intensity and volume per week via `periodization.week_modifier`. `block` and
   `emergent` insert a deload near the end of each cycle automatically.
6. **Equipment + injuries** are enforced at filtering time. If a primary
   movement is dropped by an injury (e.g. squat + knees), the swap dictionary
   substitutes a safe alternative before falling back to "anything that fits".
7. **Session duration** caps the per-day exercise count (`session_duration.cap_for`)
   and triggers superset packing of antagonists (`pack_session`) when a day
   does not fit the requested time budget.
8. After the test week the user calls `POST /workouts/{plan_id}/finalize-test-week`
   to recompute working weights for weeks 2..N from logged test sets via
   `AutoWeightCalculator` (Epley with RIR correction).
9. Continuous logging via `POST /workouts/sets` keeps `Mesocycle.weekly_volume`
   and the per-exercise e1RM up-to-date; `POST /workouts/regenerate` builds the
   next mesocycle with auto-progression and an inserted deload week.

Editing endpoints (`PUT /workouts/{plan_id}/days/{day_id}`,
`PATCH /workouts/exercises/{id}/weight`) let users override individual values;
removed exercises are remembered in `plan.params.user_edits` so future
mesocycles avoid them.

## Nutrition module

- `POST /api/nutrition/targets` runs Mifflin-St Jeor + activity factor → TDEE,
  applies goal-specific calorie multiplier (cut 0.82, maintain 1.0, bulk 1.12)
  and protein/fat per-kg targets, fills carbs from the residual.
- Meals + food entries (`POST /api/meals`, `POST /api/food-entries`) compute
  per-entry macros from `BJU/100 g × grams ÷ 100`, then `kcal = P·4 + F·9 + C·4`.
- Daily totals are aggregated server-side via `GET /api/nutrition/daily-summary`.
- All numeric inputs are validated server-side (no negatives, sane upper bounds).

## Local dev (without Docker)

```bash
# backend
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://gym:gym@localhost:5432/gym alembic upgrade head
python -m app.data.seed_exercises   # also seeds workout templates
uvicorn app.main:app --reload

# frontend
cd frontend
npm i && npm run dev
```

## Tests

```bash
cd backend
pytest -q          # 112 unit tests covering filtering, template picker,
                   # equipment / injury enforcement, nutrition schemas, etc.
```
