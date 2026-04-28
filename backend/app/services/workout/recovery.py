"""Recovery-aware day spacing for the weekly split."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

from app.models.exercise import ExerciseCategory, MuscleGroup
from app.models.user import Experience


WEEK_DAYS: Final[tuple[str, ...]] = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_TO_INDEX: Final[dict[str, int]] = {d: i for i, d in enumerate(WEEK_DAYS)}


HEAVY_PUSH_PATTERNS: Final[frozenset[str]] = frozenset({
    "bench_press_barbell",
    "incline_bench_barbell",
    "overhead_press_barbell",
})

HEAVY_LOWER_PATTERNS: Final[frozenset[str]] = frozenset({
    "back_squat_barbell",
    "deadlift_barbell",
    "romanian_deadlift_barbell",
    "leg_press_machine",
})


FATIGUE_BY_MUSCLE: Final[dict[MuscleGroup, int]] = {
    MuscleGroup.legs: 4,
    MuscleGroup.back: 4,
    MuscleGroup.chest: 3,
    MuscleGroup.shoulders: 3,
    MuscleGroup.glutes: 3,
    MuscleGroup.biceps: 1,
    MuscleGroup.triceps: 1,
    MuscleGroup.calves: 1,
    MuscleGroup.forearms: 1,
    MuscleGroup.core: 1,
    MuscleGroup.cardio: 1,
    MuscleGroup.full_body: 4,
}


FATIGUE_CAP_PER_DAY: Final[dict[Experience, int]] = {
    Experience.beginner:     10,
    Experience.intermediate: 14,
    Experience.advanced:     18,
}


@dataclass(frozen=True, slots=True)
class DayBlueprint:
    title: str
    focus: str
    is_rest: bool
    primary_muscles: tuple[MuscleGroup, ...]
    heavy_compound: bool


def fatigue_score(primary_muscles: Sequence[MuscleGroup], category: ExerciseCategory) -> int:
    base = sum(FATIGUE_BY_MUSCLE.get(m, 1) for m in primary_muscles)
    if category == ExerciseCategory.compound:
        base += 1
    return base


def fatigue_cap(experience: Experience) -> int:
    return FATIGUE_CAP_PER_DAY[experience]


def normalize_available_days(days: Sequence[str], required: int) -> list[int]:
    """Return ordered weekday indices for the user's chosen schedule.

    Falls back to evenly distributed days when the user did not specify enough.
    """
    chosen: list[int] = []
    seen: set[int] = set()
    for raw in days or ():
        key = (raw or "").strip().lower()[:3]
        if key in DAY_TO_INDEX:
            idx = DAY_TO_INDEX[key]
            if idx not in seen:
                chosen.append(idx)
                seen.add(idx)
    if len(chosen) < required:
        defaults = (0, 2, 4, 5, 1, 3, 6)
        for idx in defaults:
            if idx in seen:
                continue
            chosen.append(idx)
            seen.add(idx)
            if len(chosen) >= required:
                break
    return sorted(chosen[:required])


def space_heavy_days(blueprints: list[DayBlueprint], available_indices: list[int]) -> list[int]:
    """Return weekday indices for each blueprint, respecting 48h gap on heavy days.

    Inputs:
        blueprints in execution order
        available_indices weekday slots already chosen
    Returns weekday index list aligned to blueprints. If a heavy day collides
    with an adjacent heavy day, swap with the next non-heavy slot.
    """
    if not blueprints:
        return []
    if len(available_indices) < len(blueprints):
        available_indices = list(available_indices) + [
            i for i in range(7) if i not in available_indices
        ]
    slots = list(available_indices[: len(blueprints)])
    heavy = [bp.heavy_compound for bp in blueprints]

    for i in range(1, len(slots)):
        if not (heavy[i] and heavy[i - 1]):
            continue
        if abs(slots[i] - slots[i - 1]) >= 2:
            continue
        for j in range(i + 1, len(slots)):
            if heavy[j]:
                continue
            if abs(slots[j] - slots[i - 1]) >= 2:
                slots[i], slots[j] = slots[j], slots[i]
                heavy[i], heavy[j] = heavy[j], heavy[i]
                break
    return slots
