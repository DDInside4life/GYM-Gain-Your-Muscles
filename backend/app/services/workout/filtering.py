"""Pure exercise filtering utilities."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from app.models.exercise import Equipment, Exercise
from app.models.user import Experience


INJURY_TO_CONTRA: Final[dict[str, frozenset[str]]] = {
    "knee":      frozenset({"knee", "deep_squat", "high_impact"}),
    "back":      frozenset({"spine_load", "heavy_deadlift", "back"}),
    "lower_back": frozenset({"spine_load", "heavy_deadlift", "back"}),
    "shoulder":  frozenset({"overhead_press", "bench_heavy", "shoulder"}),
    "wrist":     frozenset({"wrist", "heavy_press"}),
    "elbow":     frozenset({"elbow"}),
    "hip":       frozenset({"hip", "deep_squat"}),
    "ankle":     frozenset({"ankle", "high_impact"}),
    "neck":      frozenset({"neck", "spine_load"}),
}


EXPERIENCE_DIFFICULTY_CAP: Final[dict[Experience, int]] = {
    Experience.beginner:     3,
    Experience.intermediate: 4,
    Experience.advanced:     5,
}


@dataclass(frozen=True, slots=True)
class FilterCriteria:
    location: str
    equipment: frozenset[Equipment]
    contraindications: frozenset[str]
    experience: Experience
    require_test: bool = False
    require_progression: bool = False


def resolve_contraindications(injuries: Iterable[str]) -> frozenset[str]:
    tokens: set[str] = set()
    for inj in injuries:
        key = (inj or "").strip().lower()
        if key in INJURY_TO_CONTRA:
            tokens |= INJURY_TO_CONTRA[key]
    return frozenset(tokens)


def is_safe(exercise: Exercise, contras: frozenset[str]) -> bool:
    if not contras:
        return True
    return not (contras & set(exercise.contraindications or []))


def matches_location(exercise: Exercise, location: str) -> bool:
    if location == "home":
        return bool(exercise.is_home)
    if location == "gym":
        return bool(exercise.is_gym)
    return True


def matches_equipment(exercise: Exercise, available: frozenset[Equipment]) -> bool:
    if not available:
        return True
    return exercise.equipment in available


def filter_pool(pool: Iterable[Exercise], criteria: FilterCriteria) -> list[Exercise]:
    cap = EXPERIENCE_DIFFICULTY_CAP[criteria.experience]
    result: list[Exercise] = []
    for ex in pool:
        if not ex.is_active:
            continue
        if not matches_location(ex, criteria.location):
            continue
        if not matches_equipment(ex, criteria.equipment):
            continue
        if not is_safe(ex, criteria.contraindications):
            continue
        if (ex.difficulty or 1) > cap:
            continue
        if criteria.require_test and not ex.suitable_for_test:
            continue
        if criteria.require_progression and not ex.suitable_for_progression:
            continue
        result.append(ex)
    return result
