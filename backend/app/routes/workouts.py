from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.models.workout import WorkoutDay, WorkoutExercise
from app.repositories.exercise import ExerciseRepository
from app.repositories.workout import WorkoutPlanRepository, WorkoutResultRepository
from app.schemas.workout import (
    WorkoutDayPatch, WorkoutFeedbackInput, WorkoutFeedbackRead, WorkoutGenerateInput, WorkoutPlanRead,
    WorkoutResultInput, WorkoutResultRead,
)
from app.services.workout import ProgressionService, WorkoutGenerator

router = APIRouter()


@router.post("/generate", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    payload: WorkoutGenerateInput, user: CurrentUser, db: DbSession,
) -> WorkoutPlanRead:
    plan = await WorkoutGenerator(db).generate(user, payload)
    return WorkoutPlanRead.model_validate(plan)


@router.get("/current", response_model=WorkoutPlanRead | None)
async def current_plan(user: CurrentUser, db: DbSession) -> WorkoutPlanRead | None:
    plan = await WorkoutPlanRepository(db).latest_for_user(user.id)
    return WorkoutPlanRead.model_validate(plan) if plan else None


@router.get("/history", response_model=list[WorkoutPlanRead])
async def history(user: CurrentUser, db: DbSession) -> list[WorkoutPlanRead]:
    items = await WorkoutPlanRepository(db).history(user.id)
    return [WorkoutPlanRead.model_validate(p) for p in items]


@router.get("/predefined", response_model=list[dict])
async def predefined_programs() -> list[dict]:
    return [
        {"id": "full_body_hypertrophy", "name": "Full Body Hypertrophy", "days_per_week": 3, "goal": "muscle_gain"},
        {"id": "upper_lower_strength", "name": "Upper / Lower Strength", "days_per_week": 4, "goal": "strength"},
        {"id": "push_pull_legs", "name": "Push Pull Legs", "days_per_week": 5, "goal": "muscle_gain"},
    ]


@router.post("/progress", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def progress(user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    current = await WorkoutPlanRepository(db).latest_for_user(user.id)
    if current is None:
        raise NotFound("No active plan")
    params = current.params or {}
    payload = WorkoutGenerateInput(
        weight_kg=float(getattr(user, "weight_kg", 75) or 75),
        height_cm=float(getattr(user, "height_cm", 175) or 175),
        age=28,
        experience=params.get("experience", getattr(user, "experience", "intermediate")),
        goal=params.get("goal", getattr(user, "goal", "muscle_gain")),
        equipment=params.get("equipment", ["bodyweight", "dumbbell", "barbell", "machine"]),
        injuries=params.get("injuries", []),
        days_per_week=int(params.get("days_per_week", 4)),
    )
    plan = await WorkoutGenerator(db).generate(user, payload)
    return WorkoutPlanRead.model_validate(plan)


@router.post("/feedback", response_model=WorkoutFeedbackRead, status_code=status.HTTP_201_CREATED)
async def feedback(
    payload: WorkoutFeedbackInput, user: CurrentUser, db: DbSession,
) -> WorkoutFeedbackRead:
    fb = await ProgressionService(db).submit_feedback(
        user, payload.day_id, payload.completed, payload.difficulty,
        payload.discomfort, payload.note,
    )
    return WorkoutFeedbackRead.model_validate(fb)


@router.get("/{plan_id}", response_model=WorkoutPlanRead)
async def get_plan(plan_id: int, user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    plan = await WorkoutPlanRepository(db).get_with_days(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("Plan not found")
    return WorkoutPlanRead.model_validate(plan)


@router.post("/{plan_id}/select", response_model=WorkoutPlanRead)
async def select_plan(plan_id: int, user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    repo = WorkoutPlanRepository(db)
    plan = await repo.mark_active(user.id, plan_id)
    if plan is None:
        raise NotFound("Plan not found")
    await db.commit()
    fresh = await repo.get_with_days(plan_id)
    assert fresh is not None
    return WorkoutPlanRead.model_validate(fresh)


@router.put("/{plan_id}/days/{day_id}", response_model=WorkoutPlanRead)
async def update_day(
    plan_id: int, day_id: int, payload: WorkoutDayPatch, user: CurrentUser, db: DbSession,
) -> WorkoutPlanRead:
    repo = WorkoutPlanRepository(db)
    plan = await repo.get_with_days(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("Plan not found")
    day = next((d for d in plan.days if d.id == day_id), None)
    if day is None:
        raise NotFound("Day not found")
    day.exercises.clear()
    for pos, item in enumerate(payload.exercises):
        day.exercises.append(WorkoutExercise(
            day_id=day.id,
            exercise_id=item.exercise_id,
            position=pos,
            sets=item.sets,
            reps_min=item.reps_min,
            reps_max=item.reps_max,
            weight_kg=item.weight_kg,
            rest_sec=item.rest_sec,
            notes=item.notes,
            target_percent_1rm=item.target_percent_1rm,
            is_test_set=item.is_test_set,
            test_instruction=item.test_instruction,
        ))
    await db.commit()
    fresh = await repo.get_with_days(plan_id)
    assert fresh is not None
    return WorkoutPlanRead.model_validate(fresh)


@router.post("/results", response_model=WorkoutResultRead, status_code=status.HTTP_201_CREATED)
async def submit_result(
    payload: WorkoutResultInput, user: CurrentUser, db: DbSession,
) -> WorkoutResultRead:
    we = await db.get(WorkoutExercise, payload.workout_exercise_id)
    if we is None:
        raise NotFound("Workout exercise not found")
    day = await db.get(WorkoutDay, we.day_id)
    if day is None:
        raise NotFound("Workout day not found")
    plan = await WorkoutPlanRepository(db).get(day.plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("Plan not found")
    exercise = await ExerciseRepository(db).get(we.exercise_id)
    if exercise is None:
        raise NotFound("Exercise not found")
    estimated = round(payload.weight_kg * (1 + payload.reps_completed / 30.0), 2)
    row = await WorkoutResultRepository(db).upsert(
        user_id=user.id,
        plan_id=plan.id,
        day_id=day.id,
        workout_exercise_id=we.id,
        exercise_id=exercise.id,
        week_index=day.week_index,
        reps_completed=payload.reps_completed,
        weight_kg=payload.weight_kg,
        estimated_1rm=estimated,
    )
    await db.commit()
    await db.refresh(row)
    return WorkoutResultRead.model_validate(row)
