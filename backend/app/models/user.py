from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.workout import WorkoutPlan
    from app.models.nutrition import NutritionPlan
    from app.models.progress import WeightEntry


class Sex(str, enum.Enum):
    male = "male"
    female = "female"


class Experience(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class Goal(str, enum.Enum):
    muscle_gain = "muscle_gain"
    fat_loss = "fat_loss"
    strength = "strength"
    endurance = "endurance"
    general = "general"


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sex: Mapped[Sex | None] = mapped_column(Enum(Sex, name="user_sex"))
    birth_date: Mapped[date | None] = mapped_column(Date)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    experience: Mapped[Experience | None] = mapped_column(Enum(Experience, name="user_experience"))
    goal: Mapped[Goal | None] = mapped_column(Enum(Goal, name="user_goal"))
    activity_factor: Mapped[float] = mapped_column(Float, default=1.55, nullable=False)

    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    nutrition_plans: Mapped[list["NutritionPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    weight_entries: Mapped[list["WeightEntry"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", order_by="WeightEntry.recorded_at",
    )

    @property
    def age(self) -> int | None:
        if not self.birth_date:
            return None
        today = date.today()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years
