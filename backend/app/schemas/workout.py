from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from app.models.user import Experience, Goal
from app.models.workout import Difficulty, ProgramPhase
from app.schemas.common import ORMModel, TimestampMixin
from app.schemas.exercise import ExerciseRead

TrainingStructure = Literal["full_body", "half_split", "upper_lower", "split"]
Periodization = Literal["dup", "block", "linear", "emergent"]
ALLOWED_DURATIONS: tuple[int, ...] = (45, 60, 90, 120, 150)


class WorkoutExplainabilityRead(BaseModel):
    reason: str
    target_percent_1rm: float | None
    based_on_e1rm: float | None


def build_workout_explainability(
    *,
    is_test_set: bool,
    weight_kg: float | None,
    target_percent_1rm: float | None,
) -> WorkoutExplainabilityRead | None:
    if target_percent_1rm is None and weight_kg is None:
        return None
    based_on_e1rm: float | None = None
    if target_percent_1rm and target_percent_1rm > 0 and weight_kg is not None:
        based_on_e1rm = round(weight_kg / target_percent_1rm, 2)
    reason = (
        "Weight is selected by test-week prescription to estimate current strength."
        if is_test_set
        else "Weight is selected from target %1RM and your latest estimated 1RM."
    )
    return WorkoutExplainabilityRead(
        reason=reason,
        target_percent_1rm=target_percent_1rm,
        based_on_e1rm=based_on_e1rm,
    )


class WorkoutGenerateInput(BaseModel):
    weight_kg: float = Field(gt=20, lt=400)
    height_cm: float = Field(gt=50, lt=260)
    age: int = Field(ge=10, le=100)
    experience: Experience
    goal: Goal
    equipment: list[str] = Field(default_factory=list, max_length=10)
    injuries: list[str] = Field(default_factory=list, max_length=10)
    days_per_week: int = Field(default=4, ge=2, le=6)

    session_duration_min: int | None = None
    training_structure: TrainingStructure | None = None
    periodization: Periodization | None = None
    cycle_length_weeks: int | None = Field(default=None, ge=3, le=16)
    priority_exercise_ids: list[int] = Field(default_factory=list, max_length=24)

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
    superset_group: int | None = None
    exercise: ExerciseRead

    @computed_field  # type: ignore[misc]
    @property
    def reps(self) -> str:
        return f"{self.reps_min}-{self.reps_max}" if self.reps_min != self.reps_max else str(self.reps_min)

    @computed_field  # type: ignore[misc]
    @property
    def explainability(self) -> WorkoutExplainabilityRead | None:
        return build_workout_explainability(
            is_test_set=self.is_test_set,
            weight_kg=self.weight_kg,
            target_percent_1rm=self.target_percent_1rm,
        )


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
    weight_kg: float | None = Field(default=None, ge=0, le=700)
    rest_sec: int = Field(default=90, ge=20, le=600)
    notes: str = Field(default="", max_length=240)
    target_percent_1rm: float | None = Field(default=None, ge=0.0, le=1.0)
    is_test_set: bool = False
    test_instruction: str = Field(default="", max_length=240)
    target_rir: float | None = Field(default=None, ge=0.0, le=10.0)
    rpe_text: str = Field(default="", max_length=200)
    superset_group: int | None = Field(default=None, ge=1, le=20)

    @model_validator(mode="after")
    def _check_reps_order(self) -> "WorkoutExercisePatch":
        if self.reps_min > self.reps_max:
            raise ValueError("reps_min не может быть больше reps_max")
        return self


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


class SetLogInput(BaseModel):
    workout_exercise_id: int = Field(gt=0)
    set_index: int = Field(ge=0, le=20)
    completed_reps: int = Field(ge=1, le=60)
    completed_weight_kg: float = Field(gt=0, lt=700)
    rir: float = Field(ge=0.0, le=10.0)


class SetLogRead(ORMModel, TimestampMixin):
    user_id: int
    plan_id: int
    day_id: int
    workout_exercise_id: int
    exercise_id: int
    week_index: int
    set_index: int
    planned_weight_kg: float | None
    completed_reps: int
    completed_weight_kg: float
    rir: float
    volume: float
    estimated_1rm: float


class WeekProgressRead(BaseModel):
    week_index: int
    completed_sets: int
    planned_sets: int
    top_e1rm_per_exercise: dict[int, float]
    week_status: Literal["complete", "in_progress", "upcoming"]


class FinalizeTestWeekRead(BaseModel):
    plan_id: int
    updated_exercises: int
    e1rm_snapshot: dict[int, float]
