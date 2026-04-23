from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.exercise import Exercise
    from app.models.user import User


class Difficulty(str, enum.Enum):
    very_easy = "very_easy"
    easy = "easy"
    ok = "ok"
    hard = "hard"
    very_hard = "very_hard"


class ProgramPhase(str, enum.Enum):
    test = "test"
    work = "work"


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    __table_args__ = (
        Index("ix_workout_plans_user_active_week", "user_id", "is_active", "week_number"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), default="Weekly Plan", nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    month_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cycle_week: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    phase: Mapped[ProgramPhase] = mapped_column(
        Enum(ProgramPhase, name="program_phase"), default=ProgramPhase.test, nullable=False,
    )
    split_type: Mapped[str] = mapped_column(String(40), default="full_body", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="workout_plans")
    days: Mapped[list["WorkoutDay"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="WorkoutDay.day_index",
    )
    results: Mapped[list["WorkoutResult"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan",
    )
    mesocycle: Mapped["Mesocycle | None"] = relationship(
        back_populates="plan", cascade="all, delete-orphan", uselist=False,
    )


class WorkoutDay(Base):
    __tablename__ = "workout_days"
    __table_args__ = (
        UniqueConstraint("plan_id", "day_index", name="uq_workout_days_plan_day"),
    )

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    focus: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    is_rest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    week_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    phase: Mapped[ProgramPhase] = mapped_column(
        Enum(ProgramPhase, name="program_phase", create_type=False),
        default=ProgramPhase.work,
        nullable=False,
    )

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="days")
    exercises: Mapped[list["WorkoutExercise"]] = relationship(
        back_populates="day", cascade="all, delete-orphan", order_by="WorkoutExercise.position",
    )
    feedback: Mapped[list["WorkoutFeedback"]] = relationship(
        back_populates="day", cascade="all, delete-orphan",
    )


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    day_id: Mapped[int] = mapped_column(
        ForeignKey("workout_days.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False, index=True,
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    reps_min: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    reps_max: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    rest_sec: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    notes: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    target_percent_1rm: Mapped[float | None] = mapped_column(Float)
    is_test_set: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    test_instruction: Mapped[str] = mapped_column(String(240), default="", nullable=False)

    day: Mapped["WorkoutDay"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()

    @property
    def reps(self) -> str:
        return f"{self.reps_min}-{self.reps_max}" if self.reps_min != self.reps_max else str(self.reps_min)


class WorkoutFeedback(Base):
    __tablename__ = "workout_feedback"
    __table_args__ = (
        UniqueConstraint("day_id", "user_id", name="uq_workout_feedback_day_user"),
    )

    day_id: Mapped[int] = mapped_column(
        ForeignKey("workout_days.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="workout_difficulty"), default=Difficulty.ok, nullable=False,
    )
    discomfort: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    note: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    day: Mapped["WorkoutDay"] = relationship(back_populates="feedback")


class WorkoutResult(Base):
    __tablename__ = "workout_results"
    __table_args__ = (
        UniqueConstraint("workout_exercise_id", "user_id", name="uq_workout_result_exercise_user"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    day_id: Mapped[int] = mapped_column(
        ForeignKey("workout_days.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    week_index: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_1rm: Mapped[float] = mapped_column(Float, nullable=False)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="results")
    exercise: Mapped["Exercise"] = relationship()


class Mesocycle(Base):
    __tablename__ = "mesocycles"
    __table_args__ = (
        UniqueConstraint("plan_id", name="uq_mesocycle_plan"),
        Index("ix_mesocycle_user_active", "user_id", "is_active"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False,
    )
    cycle_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    current_week: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_volume: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    plan: Mapped["WorkoutPlan"] = relationship(back_populates="mesocycle")


class SetLog(Base):
    __tablename__ = "set_logs"
    __table_args__ = (
        Index("ix_set_logs_user_created", "user_id", "created_at"),
        Index("ix_set_logs_plan_week", "plan_id", "week_index"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    day_id: Mapped[int] = mapped_column(
        ForeignKey("workout_days.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    workout_exercise_id: Mapped[int] = mapped_column(
        ForeignKey("workout_exercises.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    week_index: Mapped[int] = mapped_column(Integer, nullable=False)
    set_index: Mapped[int] = mapped_column(Integer, nullable=False)
    planned_weight_kg: Mapped[float | None] = mapped_column(Float)
    completed_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    rir: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_1rm: Mapped[float] = mapped_column(Float, nullable=False)


WorkoutProgram = WorkoutPlan
