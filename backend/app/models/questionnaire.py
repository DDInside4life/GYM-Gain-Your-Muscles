from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    pass


class WorkoutQuestionnaire(Base):
    __tablename__ = "workout_questionnaires"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    sex: Mapped[str] = mapped_column(String(10), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    experience: Mapped[str] = mapped_column(String(20), nullable=False)
    goal: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str] = mapped_column(String(10), nullable=False)
    equipment: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list, nullable=False)
    injuries: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list, nullable=False)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    available_days: Mapped[list[str]] = mapped_column(ARRAY(String(3)), default=list, nullable=False)
    notes: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True,
    )
