from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Meal(Base):
    __tablename__ = "nutrition_meals"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tracked_meals")
    food_entries: Mapped[list["FoodEntry"]] = relationship(
        back_populates="meal", cascade="all, delete-orphan", order_by="FoodEntry.id",
    )


class FoodEntry(Base):
    __tablename__ = "food_entries"

    meal_id: Mapped[int] = mapped_column(
        ForeignKey("nutrition_meals.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    protein_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    grams: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_protein: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_fat: Mapped[float] = mapped_column(Float, nullable=False)
    calculated_carbs: Mapped[float] = mapped_column(Float, nullable=False)
    calories: Mapped[float] = mapped_column(Float, nullable=False)

    meal: Mapped[Meal] = relationship(back_populates="food_entries")
