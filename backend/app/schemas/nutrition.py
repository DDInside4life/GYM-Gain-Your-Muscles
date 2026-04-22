from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.user import Goal, Sex
from app.schemas.common import ORMModel, TimestampMixin


class NutritionInput(BaseModel):
    weight_kg: float = Field(gt=20, lt=400)
    height_cm: float = Field(gt=50, lt=260)
    age: int = Field(ge=10, le=100)
    sex: Sex
    activity_factor: float = Field(default=1.55, ge=1.2, le=2.4)
    goal: Goal


class MealItem(BaseModel):
    name: str
    amount_g: float


class MealRead(ORMModel, TimestampMixin):
    position: int
    title: str
    calories: int
    protein_g: float
    fat_g: float
    carbs_g: float
    items: list[dict]


class NutritionPlanRead(ORMModel, TimestampMixin):
    calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    bmr: int
    tdee: int
    goal_label: str
    meals: list[MealRead]
