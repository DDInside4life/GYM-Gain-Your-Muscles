from __future__ import annotations

from app.models.exercise import ExerciseCategory, MuscleGroup
from app.models.user import Experience
from app.services.workout.recovery import (
    DayBlueprint,
    fatigue_cap,
    fatigue_score,
    normalize_available_days,
    space_heavy_days,
)


def test_normalize_available_days_pads_when_under_specified():
    days = normalize_available_days(["mon"], required=4)
    assert len(days) == 4
    assert 0 in days


def test_normalize_available_days_clamps_when_over_specified():
    days = normalize_available_days(["mon", "tue", "wed", "thu", "fri", "sat", "sun"], required=3)
    assert len(days) == 3


def test_fatigue_score_higher_for_compound_legs():
    legs_compound = fatigue_score((MuscleGroup.legs,), ExerciseCategory.compound)
    arms_isolation = fatigue_score((MuscleGroup.biceps,), ExerciseCategory.isolation)
    assert legs_compound > arms_isolation


def test_fatigue_cap_increases_with_experience():
    assert fatigue_cap(Experience.beginner) < fatigue_cap(Experience.advanced)


def test_space_heavy_days_keeps_separation():
    blueprints = [
        DayBlueprint("Толкающий", "грудь", False, (MuscleGroup.chest,), heavy_compound=True),
        DayBlueprint("Тянущий", "спина", False, (MuscleGroup.back,), heavy_compound=False),
        DayBlueprint("Ноги", "ноги", False, (MuscleGroup.legs,), heavy_compound=True),
    ]
    slots = space_heavy_days(blueprints, [0, 1, 2])
    assert len(slots) == 3
    heavy_slots = [slots[i] for i, bp in enumerate(blueprints) if bp.heavy_compound]
    assert all(abs(a - b) >= 2 for a in heavy_slots for b in heavy_slots if a != b)
