from __future__ import annotations

from datetime import date

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.intelligent_training import (
    GenerateProgramInput,
    GenerateProgramResponse,
    ProgressRead,
    TodayWorkoutRead,
    WeeklyWorkoutRead,
    WorkoutLogInput,
    WorkoutLogResponse,
)
from app.schemas.workout import WorkoutDayRead, WorkoutPlanRead
from app.services.workout import IntelligentTrainingService

router = APIRouter()


@router.post("/generate-program", response_model=GenerateProgramResponse, status_code=status.HTTP_201_CREATED)
async def generate_program(payload: GenerateProgramInput, user: CurrentUser, db: DbSession) -> GenerateProgramResponse:
    service = IntelligentTrainingService(db)
    plan, split, strength = await service.generate_program(user, payload)
    return GenerateProgramResponse(
        plan=WorkoutPlanRead.model_validate(plan),
        split=split,
        mesocycle_weeks=4,
        strength_profile=strength,
    )


@router.get("/workout/today", response_model=TodayWorkoutRead)
async def workout_today(user: CurrentUser, db: DbSession) -> TodayWorkoutRead:
    service = IntelligentTrainingService(db)
    day, cycle = await service.today_workout(user.id)
    phase = "deload" if cycle.current_week == 4 else "work"
    return TodayWorkoutRead(
        date=date.today(),
        day=WorkoutDayRead.model_validate(day) if day else None,
        week_index=cycle.current_week,
        phase=phase,
        mesocycle_number=cycle.cycle_number,
    )


@router.get("/workout/weekly", response_model=WeeklyWorkoutRead)
async def workout_weekly(user: CurrentUser, db: DbSession) -> WeeklyWorkoutRead:
    service = IntelligentTrainingService(db)
    _, cycle = await service.today_workout(user.id)
    plan = await service.plan_repo.get_with_days(cycle.plan_id)
    if plan is None:
        return WeeklyWorkoutRead(week_index=cycle.current_week, days=[])
    days = [WorkoutDayRead.model_validate(day) for day in plan.days if day.week_index == cycle.current_week]
    return WeeklyWorkoutRead(week_index=cycle.current_week, days=days)


@router.post("/workout/log", response_model=WorkoutLogResponse, status_code=status.HTTP_201_CREATED)
async def workout_log(payload: WorkoutLogInput, user: CurrentUser, db: DbSession) -> WorkoutLogResponse:
    result = await IntelligentTrainingService(db).log_workout(user, payload)
    return WorkoutLogResponse(
        updated=result.updated,
        next_weight_adjustment_pct=result.next_weight_adjustment_pct,
        weekly_volume=result.weekly_volume,
    )


@router.get("/progress", response_model=ProgressRead)
async def progress(user: CurrentUser, db: DbSession) -> ProgressRead:
    weekly_volume, strength, volume_delta_pct = await IntelligentTrainingService(db).progress(user.id)
    return ProgressRead(
        weekly_volume=weekly_volume,
        strength=strength,
        volume_delta_pct=volume_delta_pct,
    )
