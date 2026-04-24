from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.exercise import Exercise


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"
    __table_args__ = (UniqueConstraint("slug", name="uq_workout_templates_slug"),)

    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="intermediate")
    split_type: Mapped[str] = mapped_column(String(40), nullable=False)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    days: Mapped[list["TemplateDay"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateDay.day_index",
    )


class TemplateDay(Base):
    __tablename__ = "template_days"
    __table_args__ = (UniqueConstraint("template_id", "day_index", name="uq_template_days_template_day"),)

    template_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    focus: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    is_rest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    template: Mapped["WorkoutTemplate"] = relationship(back_populates="days")
    exercises: Mapped[list["TemplateExercise"]] = relationship(
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="TemplateExercise.position",
    )


class TemplateExercise(Base):
    __tablename__ = "template_exercises"
    __table_args__ = (UniqueConstraint("template_day_id", "position", name="uq_template_exercises_day_pos"),)

    template_day_id: Mapped[int] = mapped_column(
        ForeignKey("template_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sets: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    reps_min: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    reps_max: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    rest_sec: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    target_percent_1rm: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str] = mapped_column(String(240), default="", nullable=False)

    day: Mapped["TemplateDay"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()
