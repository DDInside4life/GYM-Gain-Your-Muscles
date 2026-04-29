"""Pure rule tables and helpers for workout/progression logic.

Kept free of I/O so it can be unit-tested and reused by both generator and progression.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.models.exercise import Equipment
from app.models.user import Experience, Goal
from app.models.workout import Difficulty


@dataclass(frozen=True, slots=True)
class RepScheme:
    sets: int
    reps_min: int
    reps_max: int
    rest_sec: int
    rpe: int


GOAL_SCHEME: Final[dict[Goal, RepScheme]] = {
    Goal.muscle_gain: RepScheme(4, 8, 12, 90, 8),
    Goal.fat_loss:    RepScheme(3, 12, 15, 60, 7),
    Goal.strength:    RepScheme(5, 3, 6, 180, 9),
    Goal.endurance:   RepScheme(3, 15, 20, 45, 6),
    Goal.general:     RepScheme(3, 10, 12, 75, 7),
}

EXPERIENCE_VOLUME_MOD: Final[dict[Experience, float]] = {
    Experience.beginner: 0.75,
    Experience.intermediate: 1.0,
    Experience.advanced: 1.15,
}

EXPERIENCE_INTENSITY_MOD: Final[dict[Experience, float]] = {
    Experience.beginner: 0.4,
    Experience.intermediate: 0.6,
    Experience.advanced: 0.8,
}

GOAL_INTENSITY_MOD: Final[dict[Goal, float]] = {
    Goal.strength: 1.10,
    Goal.muscle_gain: 1.00,
    Goal.fat_loss: 0.85,
    Goal.endurance: 0.70,
    Goal.general: 0.90,
}

# injury-keyword -> contraindication tokens present in seed data
INJURY_CONTRA: Final[dict[str, frozenset[str]]] = {
    "knee":     frozenset({"knee", "deep_squat"}),
    "back":     frozenset({"spine_load", "heavy_deadlift", "back"}),
    "shoulder": frozenset({"overhead_press", "bench_heavy", "shoulder"}),
    "wrist":    frozenset({"wrist", "heavy_press"}),
    "elbow":    frozenset({"elbow"}),
    "hip":      frozenset({"hip", "deep_squat"}),
}

DEFAULT_EQUIPMENT: Final[frozenset[Equipment]] = frozenset({
    Equipment.bodyweight, Equipment.dumbbell, Equipment.barbell, Equipment.machine,
})

DIFFICULTY_INTENSITY_MULT: Final[dict[Difficulty, float]] = {
    Difficulty.very_easy: 1.075,
    Difficulty.easy:      1.050,
    Difficulty.ok:        1.025,
    Difficulty.hard:      1.000,
    Difficulty.very_hard: 0.925,
}

DIFFICULTY_SETS_DELTA: Final[dict[Difficulty, int]] = {
    Difficulty.very_easy: 1,
    Difficulty.easy:      0,
    Difficulty.ok:        0,
    Difficulty.hard:      0,
    Difficulty.very_hard: -1,
}

MIN_SETS, MAX_SETS = 2, 6
MIN_EXERCISES_PER_DAY, MAX_EXERCISES_PER_DAY = 4, 6
DELOAD_EVERY_WEEKS = 4
PLATE_INCREMENT_KG = 2.5


def resolve_injury_contras(injuries: list[str]) -> frozenset[str]:
    tokens: set[str] = set()
    for inj in injuries:
        tokens |= INJURY_CONTRA.get(inj.strip().lower(), frozenset())
    return frozenset(tokens)


def round_to_plate(weight: float, plate: float = PLATE_INCREMENT_KG) -> float:
    return round(max(weight, plate) / plate) * plate


def clamp_sets(sets: int) -> int:
    return max(MIN_SETS, min(MAX_SETS, sets))


@dataclass(frozen=True, slots=True)
class AutoDeloadDecision:
    should_deload: bool
    intensity_mult: float
    sets_delta: int
    reasons: tuple[str, ...]


def decide_auto_deload(
    *,
    scheduled_deload: bool,
    e1rm_drop_ratio: float | None,
    high_effort_ratio: float | None,
    missed_session_ratio: float | None,
) -> AutoDeloadDecision:
    reasons: list[str] = []
    if e1rm_drop_ratio is not None and e1rm_drop_ratio >= 0.03:
        reasons.append("drop_e1rm_trend")
    if high_effort_ratio is not None and high_effort_ratio >= 0.5:
        reasons.append("high_effort_trend")
    if missed_session_ratio is not None and missed_session_ratio >= 0.4:
        reasons.append("missed_session_trend")

    adaptive_deload = len(reasons) >= 2
    should_deload = scheduled_deload or adaptive_deload
    if not should_deload:
        return AutoDeloadDecision(
            should_deload=False,
            intensity_mult=1.0,
            sets_delta=0,
            reasons=tuple(reasons),
        )
    return AutoDeloadDecision(
        should_deload=True,
        intensity_mult=0.88 if adaptive_deload else 0.9,
        sets_delta=-1,
        reasons=tuple(reasons) if reasons else ("scheduled_deload",),
    )


@dataclass(frozen=True, slots=True)
class ComplianceAdjustment:
    sets_delta: int
    intensity_cap: float
    reason: str


def compliance_adjustment(compliance_ratio: float | None) -> ComplianceAdjustment:
    if compliance_ratio is None:
        return ComplianceAdjustment(sets_delta=0, intensity_cap=1.0, reason="no_data")
    if compliance_ratio < 0.4:
        return ComplianceAdjustment(sets_delta=-2, intensity_cap=0.9, reason="very_low_compliance")
    if compliance_ratio < 0.6:
        return ComplianceAdjustment(sets_delta=-1, intensity_cap=0.95, reason="low_compliance")
    return ComplianceAdjustment(sets_delta=0, intensity_cap=1.0, reason="stable_compliance")
