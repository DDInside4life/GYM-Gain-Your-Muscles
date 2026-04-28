"""Exercise-specific safe starter loads (kg).

Pure logic; no database access. Used for the test week and as a fallback
when no test result exists yet.

Each `(archetype, experience)` row defines:
    `start_kg`  – conservative starter load
    `min_kg`    – never below this (technical-form floor)
    `max_kg`    – never above this (safety ceiling)
    `plate_kg`  – rounding increment
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.models.user import Experience, Goal


@dataclass(frozen=True, slots=True)
class StarterRow:
    start_kg: float | None
    min_kg: float
    max_kg: float
    plate_kg: float


_NONE_ROW = StarterRow(None, 0.0, 0.0, 1.0)


GOAL_MULT: Final[dict[Goal, float]] = {
    Goal.strength:    1.05,
    Goal.muscle_gain: 1.00,
    Goal.fat_loss:    0.85,
    Goal.endurance:   0.80,
    Goal.general:     0.90,
}


_TABLE: Final[dict[str, dict[Experience, StarterRow]]] = {
    "bench_press_barbell": {
        Experience.beginner:     StarterRow(30.0, 20.0,  60.0, 2.5),
        Experience.intermediate: StarterRow(50.0, 30.0, 100.0, 2.5),
        Experience.advanced:     StarterRow(70.0, 50.0, 140.0, 2.5),
    },
    "incline_bench_barbell": {
        Experience.beginner:     StarterRow(25.0, 20.0,  55.0, 2.5),
        Experience.intermediate: StarterRow(40.0, 25.0,  90.0, 2.5),
        Experience.advanced:     StarterRow(60.0, 40.0, 120.0, 2.5),
    },
    "back_squat_barbell": {
        Experience.beginner:     StarterRow(35.0, 20.0,  70.0, 2.5),
        Experience.intermediate: StarterRow(60.0, 30.0, 120.0, 2.5),
        Experience.advanced:     StarterRow(85.0, 50.0, 170.0, 2.5),
    },
    "deadlift_barbell": {
        Experience.beginner:     StarterRow(50.0, 30.0,  90.0, 2.5),
        Experience.intermediate: StarterRow(80.0, 50.0, 140.0, 2.5),
        Experience.advanced:     StarterRow(110.0, 70.0, 200.0, 2.5),
    },
    "romanian_deadlift_barbell": {
        Experience.beginner:     StarterRow(35.0, 20.0,  70.0, 2.5),
        Experience.intermediate: StarterRow(55.0, 30.0, 110.0, 2.5),
        Experience.advanced:     StarterRow(75.0, 45.0, 150.0, 2.5),
    },
    "overhead_press_barbell": {
        Experience.beginner:     StarterRow(20.0, 15.0,  35.0, 2.5),
        Experience.intermediate: StarterRow(30.0, 20.0,  55.0, 2.5),
        Experience.advanced:     StarterRow(45.0, 30.0,  80.0, 2.5),
    },
    "barbell_row": {
        Experience.beginner:     StarterRow(25.0, 20.0,  50.0, 2.5),
        Experience.intermediate: StarterRow(45.0, 25.0,  85.0, 2.5),
        Experience.advanced:     StarterRow(60.0, 40.0, 110.0, 2.5),
    },
    "hip_thrust_barbell": {
        Experience.beginner:     StarterRow(40.0, 20.0,  80.0, 2.5),
        Experience.intermediate: StarterRow(70.0, 40.0, 140.0, 2.5),
        Experience.advanced:     StarterRow(100.0, 60.0, 180.0, 2.5),
    },
    "machine_compound": {
        Experience.beginner:     StarterRow(30.0, 15.0,  60.0, 2.5),
        Experience.intermediate: StarterRow(55.0, 25.0,  95.0, 2.5),
        Experience.advanced:     StarterRow(80.0, 40.0, 140.0, 2.5),
    },
    "leg_press_machine": {
        Experience.beginner:     StarterRow(50.0, 30.0, 100.0, 5.0),
        Experience.intermediate: StarterRow(90.0, 50.0, 160.0, 5.0),
        Experience.advanced:     StarterRow(130.0, 80.0, 220.0, 5.0),
    },
    "machine_isolation": {
        Experience.beginner:     StarterRow(15.0,  5.0,  30.0, 2.5),
        Experience.intermediate: StarterRow(25.0, 10.0,  50.0, 2.5),
        Experience.advanced:     StarterRow(35.0, 15.0,  70.0, 2.5),
    },
    "cable_isolation": {
        Experience.beginner:     StarterRow(10.0,  5.0,  25.0, 2.5),
        Experience.intermediate: StarterRow(20.0,  7.5,  40.0, 2.5),
        Experience.advanced:     StarterRow(30.0, 10.0,  60.0, 2.5),
    },
    "dumbbell_compound": {
        Experience.beginner:     StarterRow(8.0,  4.0, 22.0, 1.0),
        Experience.intermediate: StarterRow(14.0, 6.0, 36.0, 1.0),
        Experience.advanced:     StarterRow(22.0, 10.0, 50.0, 1.0),
    },
    "dumbbell_isolation": {
        Experience.beginner:     StarterRow(5.0,  2.0, 14.0, 1.0),
        Experience.intermediate: StarterRow(8.0,  4.0, 22.0, 1.0),
        Experience.advanced:     StarterRow(12.0, 6.0, 30.0, 1.0),
    },
    "bodyweight_main":  {e: _NONE_ROW for e in Experience},
    "cardio":           {e: _NONE_ROW for e in Experience},
    "generic":          {e: _NONE_ROW for e in Experience},
}


def round_to_plate(weight: float, plate: float) -> float:
    if plate <= 0:
        return round(weight, 1)
    return round(round(max(weight, plate) / plate) * plate, 2)


def starter_row(archetype: str, experience: Experience) -> StarterRow:
    archetype_table = _TABLE.get(archetype) or _TABLE["generic"]
    return archetype_table.get(experience, archetype_table[Experience.intermediate])


def starter_weight(
    archetype: str,
    experience: Experience,
    goal: Goal,
) -> float | None:
    """Safe starter weight clamped to the experience-specific ceiling."""
    row = starter_row(archetype, experience)
    if row.start_kg is None:
        return None
    raw = row.start_kg * GOAL_MULT.get(goal, 1.0)
    clamped = max(row.min_kg, min(row.max_kg, raw))
    return round_to_plate(clamped, row.plate_kg)


def clamp_to_safety(archetype: str, experience: Experience, weight: float) -> float:
    row = starter_row(archetype, experience)
    if row.start_kg is None:
        return weight
    safe = max(row.min_kg, min(row.max_kg, weight))
    return round_to_plate(safe, row.plate_kg)


def plate_for(archetype: str) -> float:
    archetype_table = _TABLE.get(archetype) or _TABLE["generic"]
    return archetype_table[Experience.intermediate].plate_kg
