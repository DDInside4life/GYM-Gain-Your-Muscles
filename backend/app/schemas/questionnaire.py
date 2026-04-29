from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.user import Experience, Goal, Sex
from app.schemas.common import ORMModel, TimestampMixin


WEEK_DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
TrainingLocation = Literal["gym", "home"]
TrainingStructure = Literal["full_body", "half_split", "upper_lower", "split"]
Periodization = Literal["dup", "block", "linear", "emergent"]
ALLOWED_DURATIONS: tuple[int, ...] = (45, 60, 90, 120, 150)


class WorkoutQuestionnaireInput(BaseModel):
    sex: Sex
    age: int = Field(ge=12, le=90)
    height_cm: float = Field(gt=120, lt=230)
    weight_kg: float = Field(gt=30, lt=300)
    experience: Experience
    goal: Goal
    location: TrainingLocation
    equipment: list[str] = Field(default_factory=list, max_length=12)
    injuries: list[str] = Field(default_factory=list, max_length=10)
    days_per_week: int = Field(ge=2, le=6)
    available_days: list[str] = Field(default_factory=list, max_length=7)
    notes: str = Field(default="", max_length=500)

    session_duration_min: int | None = None
    training_structure: TrainingStructure | None = None
    periodization: Periodization | None = None
    cycle_length_weeks: int | None = Field(default=None, ge=3, le=16)
    priority_exercise_ids: list[int] = Field(default_factory=list, max_length=24)

    @field_validator("equipment", "injuries", mode="before")
    @classmethod
    def _strip_lower(cls, value: list[str] | None) -> list[str]:
        if not value:
            return []
        return [str(v).strip().lower() for v in value if str(v).strip()]

    @field_validator("available_days", mode="before")
    @classmethod
    def _validate_days(cls, value: list[str] | None) -> list[str]:
        if not value:
            return []
        cleaned: list[str] = []
        for raw in value:
            day = str(raw).strip().lower()[:3]
            if day in WEEK_DAYS and day not in cleaned:
                cleaned.append(day)
        return cleaned

    @field_validator("session_duration_min", mode="before")
    @classmethod
    def _validate_duration(cls, value: int | None) -> int | None:
        if value is None or value == "":
            return None
        try:
            ivalue = int(value)
        except (TypeError, ValueError):
            return None
        return min(ALLOWED_DURATIONS, key=lambda candidate: abs(candidate - ivalue))

    @field_validator("priority_exercise_ids", mode="before")
    @classmethod
    def _dedupe_priority(cls, value: list[int] | None) -> list[int]:
        if not value:
            return []
        seen: list[int] = []
        for raw in value:
            try:
                pid = int(raw)
            except (TypeError, ValueError):
                continue
            if pid > 0 and pid not in seen:
                seen.append(pid)
        return seen


class WorkoutQuestionnaireRead(ORMModel, TimestampMixin):
    user_id: int
    sex: str
    age: int
    height_cm: float
    weight_kg: float
    experience: str
    goal: str
    location: str
    equipment: list[str]
    injuries: list[str]
    days_per_week: int
    available_days: list[str]
    notes: str
    config: dict
    plan_id: int | None
    priority_exercise_ids: list[int] = Field(default_factory=list)
    session_duration_min: int | None = None
    training_structure: str | None = None
    periodization: str | None = None
    cycle_length_weeks: int | None = None
