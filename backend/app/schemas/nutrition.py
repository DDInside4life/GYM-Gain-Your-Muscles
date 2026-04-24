from __future__ import annotations

from datetime import date
from enum import Enum

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


class MealCreateInput(BaseModel):
    date: date
    name: str = Field(min_length=1, max_length=80)


class FoodEntryCreateInput(BaseModel):
    meal_id: int
    name: str = Field(min_length=1, max_length=140)
    protein_per_100g: float = Field(ge=0, le=1000)
    fat_per_100g: float = Field(ge=0, le=1000)
    carbs_per_100g: float = Field(ge=0, le=1000)
    grams: float = Field(gt=0, le=5000)


class FoodEntryRead(ORMModel, TimestampMixin):
    meal_id: int
    name: str
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    grams: float
    calculated_protein: float
    calculated_fat: float
    calculated_carbs: float
    calories: float


class MealTrackingRead(ORMModel, TimestampMixin):
    user_id: int
    date: date
    name: str
    food_entries: list[FoodEntryRead]
    total_protein: float
    total_fat: float
    total_carbs: float
    total_calories: float


class NutritionDailySummaryRead(BaseModel):
    date: date
    protein: float
    fat: float
    carbs: float
    calories: float


class NutritionCalculatorGoal(str, Enum):
    cut = "cut"
    maintain = "maintain"
    bulk = "bulk"


class NutritionCalculatorActivity(str, Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


class NutritionTargetsInput(BaseModel):
    sex: Sex
    age: int = Field(ge=10, le=100)
    weight_kg: float = Field(gt=20, lt=400)
    height_cm: float = Field(gt=50, lt=260)
    activity: NutritionCalculatorActivity
    goal: NutritionCalculatorGoal


class MacroTargetRead(BaseModel):
    grams: float
    kcal: float


class NutritionTargetsRead(BaseModel):
    bmr: float
    tdee: float
    target_calories: float
    goal: NutritionCalculatorGoal
    protein: MacroTargetRead
    fat: MacroTargetRead
    carbs: MacroTargetRead
