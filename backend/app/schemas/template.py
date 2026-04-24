from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TimestampMixin
from app.schemas.workout import WorkoutPlanRead


class TemplateExerciseRead(ORMModel, TimestampMixin):
    position: int
    sets: int
    reps_min: int
    reps_max: int
    rest_sec: int
    target_percent_1rm: float | None
    notes: str
    exercise_id: int
    exercise_name: str
    exercise_slug: str
    muscle: str


class TemplateDayRead(ORMModel, TimestampMixin):
    day_index: int
    title: str
    focus: str
    is_rest: bool
    exercises: list[TemplateExerciseRead]


class WorkoutTemplateRead(ORMModel, TimestampMixin):
    slug: str
    name: str
    level: str
    split_type: str
    days_per_week: int
    description: str
    is_active: bool
    days: list[TemplateDayRead]


class TemplateApplyInput(BaseModel):
    template_id: int = Field(gt=0)
    make_active: bool = True


class TemplateGenerateWorkoutInput(BaseModel):
    template_id: int = Field(gt=0)
    age: int = Field(ge=10, le=100, default=28)
    ai_adapt: bool = True


class TemplateApplyResponse(BaseModel):
    plan: WorkoutPlanRead
    source: str
    template_id: int
