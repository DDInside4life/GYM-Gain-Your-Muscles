from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.models.nutrition_tracking import FoodEntry, Meal
from app.models.user import User
from app.schemas.nutrition import FoodEntryRead, MealTrackingRead
from app.repositories.nutrition_tracking import FoodEntryRepository, MealRepository


@dataclass(slots=True)
class DailySummary:
    date: date
    protein: float
    fat: float
    carbs: float
    calories: float


@dataclass(slots=True)
class MealTotals:
    protein: float
    fat: float
    carbs: float
    calories: float


class NutritionTrackingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.meals = MealRepository(db)
        self.food_entries = FoodEntryRepository(db)

    @staticmethod
    def _round(value: float) -> float:
        return round(value, 2)

    def meal_totals(self, meal: Meal) -> MealTotals:
        protein = self._round(sum(entry.calculated_protein for entry in meal.food_entries))
        fat = self._round(sum(entry.calculated_fat for entry in meal.food_entries))
        carbs = self._round(sum(entry.calculated_carbs for entry in meal.food_entries))
        calories = self._round(sum(entry.calories for entry in meal.food_entries))
        return MealTotals(protein=protein, fat=fat, carbs=carbs, calories=calories)

    def meal_read(self, meal: Meal) -> MealTrackingRead:
        totals = self.meal_totals(meal)
        return MealTrackingRead(
            id=meal.id,
            created_at=meal.created_at,
            updated_at=meal.updated_at,
            user_id=meal.user_id,
            date=meal.date,
            name=meal.name,
            food_entries=[FoodEntryRead.model_validate(entry) for entry in meal.food_entries],
            total_protein=totals.protein,
            total_fat=totals.fat,
            total_carbs=totals.carbs,
            total_calories=totals.calories,
        )

    @classmethod
    def calculate_macros(
        cls,
        protein_per_100g: float,
        fat_per_100g: float,
        carbs_per_100g: float,
        grams: float,
    ) -> tuple[float, float, float, float]:
        protein = cls._round((protein_per_100g / 100.0) * grams)
        fat = cls._round((fat_per_100g / 100.0) * grams)
        carbs = cls._round((carbs_per_100g / 100.0) * grams)
        calories = cls._round((protein * 4.0) + (fat * 9.0) + (carbs * 4.0))
        return protein, fat, carbs, calories

    async def create_meal(self, user: User, meal_date: date, name: str) -> Meal:
        meal_name = name.strip()
        if not meal_name:
            raise BadRequest("Meal name is required")
        meal = await self.meals.create(user_id=user.id, date=meal_date, name=meal_name)
        await self.db.flush()
        return meal

    async def list_meals(self, user: User, meal_date: date) -> list[Meal]:
        return await self.meals.list_by_user_and_date(user.id, meal_date)

    async def add_food_entry(
        self,
        user: User,
        meal_id: int,
        name: str,
        protein_per_100g: float,
        fat_per_100g: float,
        carbs_per_100g: float,
        grams: float,
    ) -> FoodEntry:
        meal = await self.meals.get(meal_id)
        if meal is None or meal.user_id != user.id:
            raise NotFound("Meal not found")
        item_name = name.strip()
        if not item_name:
            raise BadRequest("Food name is required")

        calc_protein, calc_fat, calc_carbs, calories = self.calculate_macros(
            protein_per_100g=protein_per_100g,
            fat_per_100g=fat_per_100g,
            carbs_per_100g=carbs_per_100g,
            grams=grams,
        )
        entry = await self.food_entries.create(
            meal_id=meal.id,
            name=item_name,
            protein_per_100g=protein_per_100g,
            fat_per_100g=fat_per_100g,
            carbs_per_100g=carbs_per_100g,
            grams=grams,
            calculated_protein=calc_protein,
            calculated_fat=calc_fat,
            calculated_carbs=calc_carbs,
            calories=calories,
        )
        await self.db.flush()
        return entry

    async def delete_food_entry(self, user: User, entry_id: int) -> None:
        entry = await self.food_entries.get(entry_id)
        if entry is None:
            raise NotFound("Food entry not found")
        meal = await self.meals.get(entry.meal_id)
        if meal is None or meal.user_id != user.id:
            raise NotFound("Food entry not found")
        await self.food_entries.delete(entry)

    async def daily_summary(self, user: User, target_date: date) -> DailySummary:
        stmt = (
            select(
                func.coalesce(func.sum(FoodEntry.calculated_protein), 0.0),
                func.coalesce(func.sum(FoodEntry.calculated_fat), 0.0),
                func.coalesce(func.sum(FoodEntry.calculated_carbs), 0.0),
                func.coalesce(func.sum(FoodEntry.calories), 0.0),
            )
            .select_from(FoodEntry)
            .join(Meal, Meal.id == FoodEntry.meal_id)
            .where(Meal.user_id == user.id, Meal.date == target_date)
        )
        protein, fat, carbs, calories = (await self.db.execute(stmt)).one()
        return DailySummary(
            date=target_date,
            protein=self._round(float(protein)),
            fat=self._round(float(fat)),
            carbs=self._round(float(carbs)),
            calories=self._round(float(calories)),
        )
