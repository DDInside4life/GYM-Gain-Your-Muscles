from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.workout import WorkoutDayPatch, WorkoutExercisePatch


def _exercise(**overrides) -> dict:
    base = {"exercise_id": 1, "sets": 3, "reps_min": 8, "reps_max": 12}
    base.update(overrides)
    return base


def test_reps_min_must_not_exceed_reps_max() -> None:
    with pytest.raises(ValidationError):
        WorkoutExercisePatch(**_exercise(reps_min=12, reps_max=8))


def test_reps_min_equal_to_reps_max_is_allowed() -> None:
    p = WorkoutExercisePatch(**_exercise(reps_min=5, reps_max=5))
    assert p.reps_min == p.reps_max == 5


def test_negative_weight_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkoutExercisePatch(**_exercise(weight_kg=-1))


def test_weight_above_max_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkoutExercisePatch(**_exercise(weight_kg=701))


def test_zero_sets_rejected() -> None:
    with pytest.raises(ValidationError):
        WorkoutExercisePatch(**_exercise(sets=0))


def test_more_than_20_exercises_rejected() -> None:
    items = [_exercise() for _ in range(21)]
    with pytest.raises(ValidationError):
        WorkoutDayPatch(exercises=items)


def test_target_rir_bounds() -> None:
    with pytest.raises(ValidationError):
        WorkoutExercisePatch(**_exercise(target_rir=-1))
    with pytest.raises(ValidationError):
        WorkoutExercisePatch(**_exercise(target_rir=11))
