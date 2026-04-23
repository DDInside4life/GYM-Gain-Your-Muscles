from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.user import Experience, Goal


class AIUserContext(BaseModel):
    """Everything the agents need to know about the user. Pure, no ORM."""
    user_id: int
    age: int | None = None
    sex: str | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
    experience: Experience
    goal: Goal
    equipment: list[str] = Field(default_factory=list)
    injuries: list[str] = Field(default_factory=list)
    days_per_week: int = Field(ge=2, le=6)
    preferences: dict = Field(default_factory=dict)


class AIExerciseRef(BaseModel):
    """Reference to an exercise the LLM chose. Resolved to a real catalogue
    entry by the WorkoutAgent after validation."""
    slug: str = Field(min_length=1, max_length=80)
    sets: int = Field(ge=1, le=10)
    reps_min: int = Field(ge=1, le=50)
    reps_max: int = Field(ge=1, le=50)
    rest_sec: int = Field(ge=15, le=480)
    rpe: int = Field(ge=1, le=10, default=7)
    notes: str = Field(default="", max_length=240)

    @field_validator("reps_max")
    @classmethod
    def _max_ge_min(cls, v: int, info) -> int:
        mn = info.data.get("reps_min")
        if mn is not None and v < mn:
            return mn
        return v


class AIDayDraft(BaseModel):
    day_index: int = Field(ge=0, le=6)
    title: str = Field(min_length=1, max_length=60)
    focus: str = Field(default="", max_length=120)
    is_rest: bool = False
    exercises: list[AIExerciseRef] = Field(default_factory=list, max_length=8)


class AIWorkoutDraft(BaseModel):
    split_type: str = Field(min_length=2, max_length=40)
    rationale: str = Field(default="", max_length=600)
    days: list[AIDayDraft] = Field(min_length=1, max_length=7)


class AIProgressionDayAdjustment(BaseModel):
    day_index: int = Field(ge=0, le=6)
    intensity_mult: float = Field(ge=0.7, le=1.15)
    sets_delta: int = Field(ge=-2, le=2)
    reason: str = Field(default="", max_length=200)


class AIProgressionDraft(BaseModel):
    strategy: Literal["overload", "deload", "maintain", "volume_cut", "mixed"]
    rationale: str = Field(default="", max_length=600)
    adjustments: list[AIProgressionDayAdjustment] = Field(default_factory=list, max_length=7)


class AIMealItem(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    amount_g: float = Field(ge=1, le=2000)


class AIMealDraft(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    calories_ratio: float = Field(ge=0.05, le=0.6)
    items: list[AIMealItem] = Field(min_length=1, max_length=8)


class AINutritionDraft(BaseModel):
    rationale: str = Field(default="", max_length=600)
    meals: list[AIMealDraft] = Field(min_length=3, max_length=6)

    @field_validator("meals")
    @classmethod
    def _ratios_sum(cls, v: list[AIMealDraft]) -> list[AIMealDraft]:
        total = sum(m.calories_ratio for m in v)
        if total <= 0:
            raise ValueError("calories_ratio sum must be > 0")
        for m in v:
            m.calories_ratio = m.calories_ratio / total
        return v


class AIExplanationBlock(BaseModel):
    headline: str = Field(min_length=1, max_length=140)
    bullets: list[str] = Field(default_factory=list, max_length=6)
    warnings: list[str] = Field(default_factory=list, max_length=4)
    next_steps: list[str] = Field(default_factory=list, max_length=4)
