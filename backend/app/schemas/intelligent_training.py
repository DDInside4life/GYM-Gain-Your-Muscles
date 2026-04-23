from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.workout import WorkoutDayRead, WorkoutPlanRead


TrainingExperience = Literal["beginner", "intermediate", "advanced"]
TrainingGoal = Literal["hypertrophy", "strength", "recomposition"]
LoadMode = Literal["percent_1rm", "absolute"]


class InitialStrengthInput(BaseModel):
    exercise_id: int = Field(gt=0)
    one_rm: float | None = Field(default=None, gt=0, lt=700)
    weight_kg: float | None = Field(default=None, gt=0, lt=700)
    reps: int | None = Field(default=None, ge=1, le=30)

    @model_validator(mode="after")
    def _validate_source(self) -> "InitialStrengthInput":
        if self.one_rm is None and (self.weight_kg is None or self.reps is None):
            raise ValueError("Provide one_rm or weight_kg + reps")
        return self


class GenerateProgramInput(BaseModel):
    training_experience: TrainingExperience
    goal: TrainingGoal
    training_days: int = Field(ge=3, le=6)
    weight_kg: float = Field(gt=20, lt=400)
    height_cm: float | None = Field(default=None, gt=100, lt=260)
    initial_strength: list[InitialStrengthInput] = Field(default_factory=list, max_length=12)
    load_mode: LoadMode = "percent_1rm"
    start_kpsh: float = Field(default=24.0, ge=8, le=80)
    start_intensity_pct: float = Field(default=0.68, ge=0.5, le=0.92)
    growth_step: float = Field(default=0.08, ge=0.01, le=0.25)
    drop_step: float = Field(default=0.15, ge=0.05, le=0.35)
    wave_length: int = Field(default=4, ge=2, le=6)


class StrengthProfileRead(BaseModel):
    exercise_id: int
    actual_1rm: float | None = None
    estimated_1rm: float


class GenerateProgramResponse(BaseModel):
    plan: WorkoutPlanRead
    split: str
    mesocycle_weeks: int
    strength_profile: list[StrengthProfileRead]


class TodayWorkoutRead(BaseModel):
    date: date
    day: WorkoutDayRead | None
    week_index: int
    phase: str
    mesocycle_number: int


class WeeklyWorkoutRead(BaseModel):
    week_index: int
    days: list[WorkoutDayRead]


class WorkoutSetLogInput(BaseModel):
    workout_exercise_id: int = Field(gt=0)
    set_index: int = Field(ge=1, le=20)
    completed_reps: int = Field(ge=1, le=60)
    completed_weight_kg: float = Field(gt=0, lt=700)
    rir: float = Field(ge=0, le=10)


class WorkoutLogInput(BaseModel):
    sets: list[WorkoutSetLogInput] = Field(min_length=1, max_length=30)


class WorkoutLogResponse(BaseModel):
    updated: int
    next_weight_adjustment_pct: float
    weekly_volume: float


class ProgressPoint(BaseModel):
    at: datetime
    exercise_id: int
    estimated_1rm: float
    volume: float


class ProgressRead(BaseModel):
    weekly_volume: dict[str, float]
    strength: list[ProgressPoint]
    volume_delta_pct: float
