from __future__ import annotations

from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import Experience, Goal, Sex
from app.schemas.common import ORMModel, TimestampMixin


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    sex: Sex | None = None
    birth_date: date | None = None
    height_cm: float | None = Field(default=None, gt=50, lt=260)
    weight_kg: float | None = Field(default=None, gt=20, lt=400)
    experience: Experience | None = None
    goal: Goal | None = None
    activity_factor: float | None = Field(default=None, ge=1.2, le=2.4)
    global_restrictions: list[str] | None = Field(default=None, max_length=20)
    priority_exercise_ids: list[int] | None = Field(default=None, max_length=24)

    @field_validator("global_restrictions", mode="before")
    @classmethod
    def _normalize_restrictions(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        seen: list[str] = []
        for raw in value:
            token = str(raw).strip().lower()
            if token and token not in seen:
                seen.append(token)
        return seen

    @field_validator("priority_exercise_ids", mode="before")
    @classmethod
    def _dedupe_priority(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        seen: list[int] = []
        for raw in value:
            try:
                pid = int(raw)
            except (TypeError, ValueError):
                continue
            if pid > 0 and pid not in seen:
                seen.append(pid)
        return seen


class UserRead(ORMModel, TimestampMixin):
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_admin: bool
    sex: Sex | None
    birth_date: date | None
    height_cm: float | None
    weight_kg: float | None
    experience: Experience | None
    goal: Goal | None
    activity_factor: float
    global_restrictions: list[str] = Field(default_factory=list)
    priority_exercise_ids: list[int] = Field(default_factory=list)


class WeightEntryCreate(BaseModel):
    weight_kg: float = Field(gt=20, lt=400)
    recorded_at: date


class WeightEntryRead(ORMModel, TimestampMixin):
    weight_kg: float
    recorded_at: date
