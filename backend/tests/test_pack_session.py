"""Unit tests for pack_session in session_duration.py."""
import pytest

from app.services.workout.session_duration import pack_session, _estimate_min, PackedExercise


def _make_compound(exercise_id: int, muscles: list[str] | None = None) -> dict:
    return {
        "exercise_id": exercise_id,
        "sets": 4,
        "reps_min": 6,
        "reps_max": 10,
        "category": "compound",
        "primary_muscles": muscles or ["chest"],
        "superset_group": None,
    }


def _make_isolation(exercise_id: int, muscles: list[str] | None = None) -> dict:
    return {
        "exercise_id": exercise_id,
        "sets": 3,
        "reps_min": 10,
        "reps_max": 15,
        "category": "isolation",
        "primary_muscles": muscles or ["bicep"],
        "superset_group": None,
    }


def test_no_trimming_when_fits():
    exercises = [_make_compound(1), _make_compound(2)]
    result = pack_session(exercises, limit_min=120)
    assert result.isolation_exercises_removed == 0
    assert result.isolation_sets_cut == 0
    assert result.estimated_min <= 120


def test_antagonist_supersets_created():
    exercises = [
        _make_compound(1, ["push"]),
        _make_compound(2, ["pull"]),
        _make_isolation(3),
        _make_isolation(4),
        _make_isolation(5),
        _make_isolation(6),
    ]
    result = pack_session(exercises, limit_min=30)
    groups = {ex.superset_group for ex in result.exercises if ex.superset_group is not None}
    assert result.superset_pairs_added > 0 or result.isolation_exercises_removed > 0


def test_isolation_removed_when_too_long():
    exercises = [
        _make_compound(1),
        _make_compound(2),
        _make_compound(3),
        _make_isolation(4),
        _make_isolation(5),
        _make_isolation(6),
        _make_isolation(7),
    ]
    result = pack_session(exercises, limit_min=30)
    remaining_isolations = [ex for ex in result.exercises if not ex.is_compound]
    assert len(remaining_isolations) < 4 or result.isolation_sets_cut > 0


def test_compound_never_removed():
    exercises = [
        _make_compound(1),
        _make_compound(2),
        _make_isolation(3),
        _make_isolation(4),
    ]
    result = pack_session(exercises, limit_min=10)
    remaining_compound = [ex for ex in result.exercises if ex.is_compound]
    assert len(remaining_compound) == 2


def test_empty_exercises():
    result = pack_session([], limit_min=60)
    assert result.exercises == []
    assert result.estimated_min == pytest.approx(8.0, abs=1)


def test_deload_week_indices():
    from app.services.workout.next_mesocycle import deload_week_indices
    assert deload_week_indices(4) == [4]
    assert deload_week_indices(8) == [4, 8]
    assert 4 in deload_week_indices(6)
    assert deload_week_indices(2) == []
