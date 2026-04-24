from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.nutrition_tracking import FoodEntry, Meal
from app.repositories.base import BaseRepository


class MealRepository(BaseRepository[Meal]):
    model = Meal

    async def list_by_user_and_date(self, user_id: int, meal_date: date) -> list[Meal]:
        stmt = (
            select(Meal)
            .where(Meal.user_id == user_id, Meal.date == meal_date)
            .order_by(Meal.id.asc())
            .options(selectinload(Meal.food_entries))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_with_entries(self, meal_id: int) -> Meal | None:
        stmt = select(Meal).where(Meal.id == meal_id).options(selectinload(Meal.food_entries))
        res = await self.db.execute(stmt)
        return res.scalars().first()


class FoodEntryRepository(BaseRepository[FoodEntry]):
    model = FoodEntry
