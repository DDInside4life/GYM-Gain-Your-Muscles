from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.exercise import Equipment, ExerciseCategory, MuscleGroup
from app.schemas.common import ORMModel, TimestampMixin


class ExerciseBase(BaseModel):
    slug: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=120)
    description: str = ""
    primary_muscle: MuscleGroup
    secondary_muscles: list[str] = []
    equipment: Equipment
    category: ExerciseCategory
    difficulty: int = Field(default=1, ge=1, le=5)
    contraindications: list[str] = []
    image_url: str | None = None
    is_active: bool = True


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    primary_muscle: MuscleGroup | None = None
    secondary_muscles: list[str] | None = None
    equipment: Equipment | None = None
    category: ExerciseCategory | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    contraindications: list[str] | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ExerciseRead(ORMModel, TimestampMixin, ExerciseBase):
    pass
