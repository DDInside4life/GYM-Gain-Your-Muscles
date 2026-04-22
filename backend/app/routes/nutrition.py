from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.schemas.nutrition import NutritionInput, NutritionPlanRead
from app.services.nutrition import NutritionService

router = APIRouter()


@router.post("/generate", response_model=NutritionPlanRead, status_code=status.HTTP_201_CREATED)
async def generate(payload: NutritionInput, user: CurrentUser, db: DbSession) -> NutritionPlanRead:
    plan = await NutritionService(db).generate_for(user, payload)
    return NutritionPlanRead.model_validate(plan)
