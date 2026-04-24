from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.nutrition import (
    MacroTargetRead,
    NutritionDailySummaryRead,
    NutritionInput,
    NutritionPlanRead,
    NutritionTargetsInput,
    NutritionTargetsRead,
)
from app.services.nutrition import NutritionService
from app.services.nutrition_tracking import NutritionTrackingService

router = APIRouter()


@router.post("/generate", response_model=NutritionPlanRead, status_code=status.HTTP_201_CREATED)
async def generate(payload: NutritionInput, user: CurrentUser, db: DbSession) -> NutritionPlanRead:
    plan = await NutritionService(db).generate_for(user, payload)
    return NutritionPlanRead.model_validate(plan)


@router.post("/targets", response_model=NutritionTargetsRead)
async def calculate_targets(payload: NutritionTargetsInput, user: CurrentUser, db: DbSession) -> NutritionTargetsRead:
    targets = NutritionService(db).calculate_targets(payload)
    return NutritionTargetsRead(
        bmr=targets.bmr,
        tdee=targets.tdee,
        target_calories=targets.target_calories,
        goal=targets.goal,
        protein=MacroTargetRead(grams=targets.protein.grams, kcal=targets.protein.kcal),
        fat=MacroTargetRead(grams=targets.fat.grams, kcal=targets.fat.kcal),
        carbs=MacroTargetRead(grams=targets.carbs.grams, kcal=targets.carbs.kcal),
    )


@router.get("/daily-summary", response_model=NutritionDailySummaryRead)
async def daily_summary(
    user: CurrentUser,
    db: DbSession,
    target_date: date = Query(..., alias="date"),
) -> NutritionDailySummaryRead:
    summary = await NutritionTrackingService(db).daily_summary(user=user, target_date=target_date)
    return NutritionDailySummaryRead(
        date=summary.date,
        protein=summary.protein,
        fat=summary.fat,
        carbs=summary.carbs,
        calories=summary.calories,
    )
