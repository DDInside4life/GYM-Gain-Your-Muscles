# GYM: Workout Reprocessing — Guide for Diploma Defense

## 1) What this project is in simple words

This is a fitness web app with:
- **backend**: business logic and database API (FastAPI + PostgreSQL),
- **frontend**: user interface in browser (Next.js),
- **infrastructure**: Docker Compose runs all services together.

The implemented feature is a full **workout reprocessing pipeline**:
- user fills workout questionnaire,
- system generates a multi-week plan,
- first week is a **test week**,
- user logs real set results,
- system recalculates working weights automatically for next weeks,
- after cycle completion, system generates next cycle with progression.

---

## 2) What problem was solved

Before rework, generation was partly template-driven and had duplicated logic paths.  
Now generation is centralized, predictable, and data-driven:

- one core generator service builds plans,
- templates are used only as **read-only references**,
- progression is based on actual user performance (sets/reps/weight/RIR),
- session duration and safety constraints are respected,
- injury-aware substitutions are integrated.

In short: **from static templates to adaptive training system**.

---

## 3) Architecture (easy explanation)

The project follows layered logic (close to clean architecture):

- **Routes (API layer)**  
  Receive HTTP requests, validate access, call services, return response.

- **Services (business logic)**  
  Core algorithms: generation, progression, periodization, weight calculation, session packing.

- **Repositories (data access)**  
  Read/write domain entities in DB.

- **Models/Schemas**  
  DB entities + request/response contracts.

This separation makes code easier to maintain, test, and explain.

---

## 4) Main user flow (what to show at defense)

### Step A — Create plan from questionnaire
User opens workout generation page and fills full questionnaire:
- profile parameters,
- goal and schedule,
- training parameters,
- restrictions and priorities.

Backend builds full plan with:
- weeks,
- days,
- exercises,
- sets/reps/rest,
- test-week metadata.

### Step B — Execute test week
In workout runner page user logs each set:
- completed reps,
- used weight,
- RIR.

These logs are stored as `SetLog`.

### Step C — Finalize test week
User presses finalize action.  
Backend computes e1RM for exercises and updates working weeks.

### Step D — Continue / regenerate cycle
After cycle completion user can generate next mesocycle with progression.

---

## 5) Key domain logic (important to explain to commission)

## 5.1 Test week
- Week 1 is test-oriented.
- For test-suitable exercises: dedicated test prescription (RIR=2).
- For non-test exercises: light base variant (higher reserve).

Why: safe calibration of actual performance before heavier working blocks.

## 5.2 e1RM and auto-weight
Estimated 1RM is computed from real logged data:

- base formula: Epley,
- corrected with RIR (unused reps reserve).

Then working weight is chosen by:
- goal-specific intensity percent,
- safety clamps,
- plate rounding.

Why: avoid random weights and personalize load progression.

## 5.3 Progression across mesocycles
- old active mesocycle is closed,
- new mesocycle is created,
- progression strategy applies (double progression style rules),
- cycle metadata is persisted.

## 5.4 Session duration control
If session is too long:
- pair antagonist movements as supersets,
- reduce isolation volume,
- remove least-critical isolation if still over limit.

Why: plan remains realistic for user’s available time.

## 5.5 Injury-aware substitutions
If exercise conflicts with injuries/constraints:
- swap dictionary proposes safer alternatives.

Why: practical safety and continuity of training plan.

---

## 6) New and changed technical components

### Backend
- New services:
  - `auto_weights.py`
  - `next_mesocycle.py`
  - `swap_dictionary.py`
- Extended:
  - `generator.py`
  - `load_progression.py`
  - `session_duration.py`
  - `filtering.py`
- API updates in:
  - `routes/workouts.py`
  - `routes/questionnaires.py`
  - `routes/templates.py`
- Added DTO/contracts in `schemas/workout.py`
- Added repository methods for mesocycle/set logs
- Added migration for `superset_group`

### Frontend
- Full questionnaire generation screen,
- day runner screen with set logging,
- finalize-test-week screen,
- history screen with inline SVG e1RM chart,
- new reusable components for set logging and rest timer,
- API client extended with new endpoints.

---

## 7) Data model additions (what to mention clearly)

- `WorkoutExercise.superset_group`  
  Marks exercises grouped into supersets.

- `SetLog` usage expanded  
  Becomes core source of factual performance for progression.

- Mesocycle metadata updates  
  Keeps cycle-level state and audit info.

---

## 8) API endpoints to mention at defense

Core operations:
- plan generation from questionnaire,
- set logging,
- test-week finalization,
- weekly progress retrieval,
- cycle regeneration.

Supporting operations:
- current/history plan access,
- read-only templates/predefined lists.

---

## 9) Testing and verification

The implementation is covered by unit/service tests for:
- progression logic,
- test-week rules,
- auto-weight calculations,
- session packing,
- swap dictionary behavior,
- questionnaire/schema validity.

Practical verification done by:
- backend test suite in container,
- frontend production build,
- full Docker Compose rebuild and healthy service checks.

---

## 10) Why this is a strong diploma project

Because it demonstrates:
- real fullstack architecture (frontend + backend + DB + infra),
- domain-driven business logic (not CRUD-only),
- algorithmic personalization,
- safety constraints and edge-case handling,
- measurable engineering quality (tests + reproducible build).

---

## 11) Ready defense script (3–5 minutes)

You can say:

1. "The goal was to transform workout generation from static template usage into adaptive progression based on user data."
2. "I centralized generation in one service and removed duplicated generation paths."
3. "I implemented a test week as calibration stage and added set-level logging."
4. "From logged results, the system computes e1RM and recalculates working loads automatically."
5. "I added progression between mesocycles, injury-aware substitutions, and duration-aware session packing."
6. "I validated the feature with backend tests, frontend production build, and full Docker deployment."

---

## 12) Typical committee questions and strong answers

### Q: Why not keep template generation only?
**A:** Templates are useful as references but too rigid for personalization.  
The new flow uses real user inputs and actual performance logs, which is required for adaptive training.

### Q: Why test week first?
**A:** It reduces risk and calibrates intensity from real performance before working blocks.

### Q: Why use set-level logs instead of only final workout result?
**A:** Set-level granularity captures fatigue and true capacity better, enabling more accurate progression.

### Q: How did you ensure maintainability?
**A:** Separated API/business/data layers, small focused services, explicit schemas, and automated tests.

### Q: How can this scale further?
**A:** Add richer analytics, coach dashboards, and model-driven progression while preserving current service boundaries.

---

## 13) Demo checklist (quick)

1. Open generation page and fill questionnaire.
2. Generate plan and show week 1 test markers.
3. Open day runner, log multiple sets.
4. Run "finalize test week", show updated working weights.
5. Open history and show e1RM trend chart.
6. Regenerate next cycle and show continuity.

---

## 14) Short conclusion

This work delivers a production-ready adaptive training module:
- personalized,
- data-driven,
- testable,
- deployable,
- understandable for real users and evaluators.

