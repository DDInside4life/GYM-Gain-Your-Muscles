from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.nutrition import MealCreateInput, MealTrackingRead
from app.services.nutrition_tracking import NutritionTrackingService

router = APIRouter()


@router.post("", response_model=MealTrackingRead, status_code=status.HTTP_201_CREATED)
async def create_meal(payload: MealCreateInput, user: CurrentUser, db: DbSession) -> MealTrackingRead:
    service = NutritionTrackingService(db)
    meal = await service.create_meal(user=user, meal_date=payload.date, name=payload.name)
    await db.commit()
    created = await service.meals.get_with_entries(meal.id)
    assert created is not None
    return service.meal_read(created)


@router.get("", response_model=list[MealTrackingRead])
async def list_meals(
    user: CurrentUser,
    db: DbSession,
    date: date = Query(...),
) -> list[MealTrackingRead]:
    service = NutritionTrackingService(db)
    meals = await service.list_meals(user=user, meal_date=date)
    return [service.meal_read(meal) for meal in meals]
