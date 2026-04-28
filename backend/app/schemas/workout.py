from __future__ import annotations

from pydantic import BaseModel, Field, computed_field, model_validator

from app.models.user import Experience, Goal
from app.models.workout import Difficulty, ProgramPhase
from app.schemas.common import ORMModel, TimestampMixin
from app.schemas.exercise import ExerciseRead


class WorkoutGenerateInput(BaseModel):
    weight_kg: float = Field(gt=20, lt=400)
    height_cm: float = Field(gt=50, lt=260)
    age: int = Field(ge=10, le=100)
    experience: Experience
    goal: Goal
    equipment: list[str] = Field(default_factory=list, max_length=10)
    injuries: list[str] = Field(default_factory=list, max_length=10)
    days_per_week: int = Field(default=4, ge=2, le=6)


class WorkoutExerciseRead(ORMModel, TimestampMixin):
    position: int
    sets: int
    reps_min: int
    reps_max: int
    weight_kg: float | None
    rest_sec: int
    notes: str
    target_percent_1rm: float | None = None
    is_test_set: bool = False
    test_instruction: str = ""
    target_rir: float | None = None
    rpe_text: str = ""
    exercise: ExerciseRead

    @computed_field  # type: ignore[misc]
    @property
    def reps(self) -> str:
        return f"{self.reps_min}-{self.reps_max}" if self.reps_min != self.reps_max else str(self.reps_min)


class WorkoutDayRead(ORMModel, TimestampMixin):
    day_index: int
    title: str
    focus: str
    is_rest: bool
    week_index: int
    phase: ProgramPhase
    exercises: list[WorkoutExerciseRead]


class WorkoutPlanRead(ORMModel, TimestampMixin):
    name: str
    week_number: int
    month_index: int
    cycle_week: int
    phase: ProgramPhase
    split_type: str
    is_active: bool
    days: list[WorkoutDayRead]
    params: dict


class WorkoutFeedbackInput(BaseModel):
    day_id: int = Field(gt=0)
    completed: bool
    difficulty: Difficulty
    discomfort: list[str] = Field(default_factory=list, max_length=10)
    note: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def _lower_discomfort(self) -> "WorkoutFeedbackInput":
        self.discomfort = [d.strip().lower() for d in self.discomfort if d.strip()]
        return self


class WorkoutFeedbackRead(ORMModel, TimestampMixin):
    day_id: int
    completed: bool
    difficulty: Difficulty
    discomfort: list[str]
    note: str


class WorkoutExercisePatch(BaseModel):
    id: int | None = Field(default=None, gt=0)
    exercise_id: int = Field(gt=0)
    sets: int = Field(ge=1, le=8)
    reps_min: int = Field(ge=1, le=30)
    reps_max: int = Field(ge=1, le=30)
    weight_kg: float | None = Field(default=None, ge=0)
    rest_sec: int = Field(default=90, ge=20, le=600)
    notes: str = Field(default="", max_length=240)
    target_percent_1rm: float | None = Field(default=None, ge=0.0, le=1.0)
    is_test_set: bool = False
    test_instruction: str = Field(default="", max_length=240)
    target_rir: float | None = Field(default=None, ge=0.0, le=10.0)
    rpe_text: str = Field(default="", max_length=200)


class WorkoutDayPatch(BaseModel):
    exercises: list[WorkoutExercisePatch] = Field(default_factory=list, max_length=20)


class WorkoutResultInput(BaseModel):
    workout_exercise_id: int = Field(gt=0)
    reps_completed: int = Field(ge=1, le=60)
    weight_kg: float = Field(gt=0, lt=700)


class WorkoutResultRead(ORMModel, TimestampMixin):
    user_id: int
    plan_id: int
    day_id: int
    workout_exercise_id: int
    exercise_id: int
    week_index: int
    reps_completed: int
    weight_kg: float
    estimated_1rm: float
