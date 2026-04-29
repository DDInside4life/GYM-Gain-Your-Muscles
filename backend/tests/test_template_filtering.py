"""Unit tests for the template-driven exercise filter.

These cover the critical product rule: an exercise from the chosen template
must be dropped at materialization time when its equipment is not in the user's
``equipment`` set or its contraindications collide with the user's injuries.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.exercise import Equipment
from app.services.workout.template_programs import (
    _is_exercise_allowed,
    _parse_equipment,
    criteria_from,
)


@dataclass
class FakeExercise:
    equipment: Equipment
    contraindications: list[str] = field(default_factory=list)
    is_active: bool = True


def test_parse_equipment_lowercases_and_validates() -> None:
    parsed = _parse_equipment(["BodyWeight", "barbell", "garbage", ""])
    assert parsed == frozenset({Equipment.bodyweight, Equipment.barbell})


def test_parse_equipment_empty_returns_empty_set() -> None:
    assert _parse_equipment(None) == frozenset()
    assert _parse_equipment([]) == frozenset()


def test_allowed_when_no_equipment_constraint() -> None:
    ex = FakeExercise(Equipment.barbell)
    assert _is_exercise_allowed(ex, equipment=frozenset(), contraindications=frozenset())


def test_allowed_when_equipment_in_set() -> None:
    ex = FakeExercise(Equipment.dumbbell)
    assert _is_exercise_allowed(
        ex,
        equipment=frozenset({Equipment.dumbbell, Equipment.bodyweight}),
        contraindications=frozenset(),
    )


def test_blocked_when_equipment_not_in_set() -> None:
    ex = FakeExercise(Equipment.barbell)
    assert not _is_exercise_allowed(
        ex,
        equipment=frozenset({Equipment.bodyweight}),
        contraindications=frozenset(),
    )


def test_blocked_when_contraindication_overlap() -> None:
    ex = FakeExercise(Equipment.barbell, contraindications=["heavy_deadlift"])
    assert not _is_exercise_allowed(
        ex,
        equipment=frozenset(),
        contraindications=frozenset({"heavy_deadlift"}),
    )


def test_inactive_exercise_always_blocked() -> None:
    ex = FakeExercise(Equipment.bodyweight, is_active=False)
    assert not _is_exercise_allowed(ex, equipment=frozenset(), contraindications=frozenset())


def test_criteria_from_normalizes_strings() -> None:
    criteria = criteria_from(
        goal="muscle_gain",
        days_per_week=4,
        training_structure="upper_lower",
        equipment=["BodyWeight", "Barbell"],
        injuries=[" Knees ", "BACK", ""],
    )
    assert criteria.equipment == frozenset({Equipment.bodyweight, Equipment.barbell})
    assert criteria.injuries == ("knees", "back")
    assert criteria.goal is not None and criteria.goal.value == "muscle_gain"


def test_criteria_from_invalid_goal_drops_to_none() -> None:
    criteria = criteria_from(goal="not_a_real_goal")
    assert criteria.goal is None


def test_criteria_from_handles_no_inputs() -> None:
    criteria = criteria_from()
    assert criteria.goal is None
    assert criteria.equipment == frozenset()
    assert criteria.injuries == ()


def test_bodyweight_only_drops_barbell_template_items() -> None:
    """End-to-end product rule: bodyweight users never see barbell exercises."""
    items = [
        FakeExercise(Equipment.bodyweight),
        FakeExercise(Equipment.barbell),
        FakeExercise(Equipment.dumbbell),
        FakeExercise(Equipment.machine),
    ]
    equipment = frozenset({Equipment.bodyweight})
    survivors = [
        ex for ex in items
        if _is_exercise_allowed(ex, equipment=equipment, contraindications=frozenset())
    ]
    assert len(survivors) == 1
    assert survivors[0].equipment == Equipment.bodyweight
