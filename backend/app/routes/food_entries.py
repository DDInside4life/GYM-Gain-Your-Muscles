from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.nutrition import FoodEntryCreateInput, FoodEntryRead
from app.services.nutrition_tracking import NutritionTrackingService

router = APIRouter()


@router.post("", response_model=FoodEntryRead, status_code=status.HTTP_201_CREATED)
async def create_food_entry(
    payload: FoodEntryCreateInput,
    user: CurrentUser,
    db: DbSession,
) -> FoodEntryRead:
    service = NutritionTrackingService(db)
    entry = await service.add_food_entry(
        user=user,
        meal_id=payload.meal_id,
        name=payload.name,
        protein_per_100g=payload.protein_per_100g,
        fat_per_100g=payload.fat_per_100g,
        carbs_per_100g=payload.carbs_per_100g,
        grams=payload.grams,
    )
    await db.commit()
    await db.refresh(entry)
    return FoodEntryRead.model_validate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food_entry(entry_id: int, user: CurrentUser, db: DbSession) -> Response:
    service = NutritionTrackingService(db)
    await service.delete_food_entry(user=user, entry_id=entry_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
