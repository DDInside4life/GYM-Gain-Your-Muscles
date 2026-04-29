from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.nutrition import (
    FoodEntryCreateInput,
    MealCreateInput,
    NutritionCalculatorActivity,
    NutritionCalculatorGoal,
    NutritionTargetsInput,
)
from app.models.user import Sex


def test_meal_name_whitespace_rejected() -> None:
    with pytest.raises(ValidationError):
        MealCreateInput(date=date.today(), name="   ")


def test_meal_name_empty_rejected() -> None:
    with pytest.raises(ValidationError):
        MealCreateInput(date=date.today(), name="")


def test_meal_name_trimmed() -> None:
    meal = MealCreateInput(date=date.today(), name="  Завтрак  ")
    assert meal.name == "Завтрак"


def test_food_entry_negative_macros_rejected() -> None:
    with pytest.raises(ValidationError):
        FoodEntryCreateInput(
            meal_id=1, name="x",
            protein_per_100g=-1, fat_per_100g=0, carbs_per_100g=0, grams=100,
        )


def test_food_entry_zero_grams_rejected() -> None:
    with pytest.raises(ValidationError):
        FoodEntryCreateInput(
            meal_id=1, name="x",
            protein_per_100g=0, fat_per_100g=0, carbs_per_100g=0, grams=0,
        )


def test_food_entry_meal_id_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        FoodEntryCreateInput(
            meal_id=0, name="x",
            protein_per_100g=0, fat_per_100g=0, carbs_per_100g=0, grams=100,
        )


def test_food_entry_blank_name_rejected() -> None:
    with pytest.raises(ValidationError):
        FoodEntryCreateInput(
            meal_id=1, name="\t \n",
            protein_per_100g=0, fat_per_100g=0, carbs_per_100g=0, grams=100,
        )


def test_targets_input_validates_age_bounds() -> None:
    with pytest.raises(ValidationError):
        NutritionTargetsInput(
            sex=Sex.male, age=5, weight_kg=70, height_cm=180,
            activity=NutritionCalculatorActivity.moderate,
            goal=NutritionCalculatorGoal.maintain,
        )
    with pytest.raises(ValidationError):
        NutritionTargetsInput(
            sex=Sex.male, age=120, weight_kg=70, height_cm=180,
            activity=NutritionCalculatorActivity.moderate,
            goal=NutritionCalculatorGoal.maintain,
        )


def test_targets_input_weight_lower_bound_strict() -> None:
    with pytest.raises(ValidationError):
        NutritionTargetsInput(
            sex=Sex.male, age=30, weight_kg=20, height_cm=180,
            activity=NutritionCalculatorActivity.moderate,
            goal=NutritionCalculatorGoal.maintain,
        )
