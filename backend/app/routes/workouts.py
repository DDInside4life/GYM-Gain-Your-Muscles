from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.repositories.workout import WorkoutPlanRepository
from app.schemas.workout import (
    WorkoutFeedbackInput, WorkoutFeedbackRead, WorkoutGenerateInput, WorkoutPlanRead,
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


@router.post("/progress", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def progress(user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    plan = await ProgressionService(db).advance(user)
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
