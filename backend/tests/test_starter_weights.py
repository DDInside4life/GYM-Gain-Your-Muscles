from __future__ import annotations

import pytest

from app.models.user import Experience, Goal
from app.services.workout.starter_weights import (
    clamp_to_safety,
    plate_for,
    round_to_plate,
    starter_row,
    starter_weight,
)


def test_round_to_plate_uses_increment():
    assert round_to_plate(38.7, 2.5) == 37.5
    assert round_to_plate(39.5, 2.5) == 40.0
    assert round_to_plate(0.0, 2.5) == 2.5  # floor at one plate
    assert round_to_plate(20.4, 2.5) == 20.0


@pytest.mark.parametrize("experience", list(Experience))
def test_bench_starter_within_safe_range(experience: Experience):
    weight = starter_weight("bench_press_barbell", experience, Goal.muscle_gain)
    row = starter_row("bench_press_barbell", experience)
    assert weight is not None
    assert row.min_kg <= weight <= row.max_kg


def test_strength_goal_increases_load_within_ceiling():
    base = starter_weight("back_squat_barbell", Experience.intermediate, Goal.muscle_gain)
    strong = starter_weight("back_squat_barbell", Experience.intermediate, Goal.strength)
    assert base is not None and strong is not None
    assert strong >= base
    row = starter_row("back_squat_barbell", Experience.intermediate)
    assert strong <= row.max_kg


def test_cutting_goal_reduces_load():
    base = starter_weight("bench_press_barbell", Experience.intermediate, Goal.muscle_gain)
    cut = starter_weight("bench_press_barbell", Experience.intermediate, Goal.fat_loss)
    assert base is not None and cut is not None
    assert cut < base


def test_clamp_to_safety_caps_dangerous_weight():
    safe = clamp_to_safety("bench_press_barbell", Experience.beginner, 999.0)
    row = starter_row("bench_press_barbell", Experience.beginner)
    assert safe == row.max_kg


def test_clamp_to_safety_floors_minimum():
    safe = clamp_to_safety("bench_press_barbell", Experience.beginner, 1.0)
    row = starter_row("bench_press_barbell", Experience.beginner)
    assert safe == row.min_kg


def test_bodyweight_returns_none():
    assert starter_weight("bodyweight_main", Experience.intermediate, Goal.muscle_gain) is None
    assert starter_weight("cardio", Experience.advanced, Goal.fat_loss) is None


def test_plate_for_known_archetype():
    assert plate_for("bench_press_barbell") == 2.5
    assert plate_for("dumbbell_isolation") == 1.0
    assert plate_for("leg_press_machine") == 5.0


def test_unknown_archetype_uses_generic_row():
    assert starter_weight("unknown-archetype", Experience.intermediate, Goal.muscle_gain) is None
