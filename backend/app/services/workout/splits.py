from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.models.exercise import MuscleGroup
from app.models.user import Experience


@dataclass(frozen=True, slots=True)
class DayTemplate:
    title: str
    muscles: tuple[MuscleGroup, ...]


SPLITS: Final[dict[str, tuple[DayTemplate, ...]]] = {
    "full_body": (
        DayTemplate("Full A", (MuscleGroup.legs, MuscleGroup.chest, MuscleGroup.back, MuscleGroup.core)),
        DayTemplate("Full B", (MuscleGroup.legs, MuscleGroup.shoulders, MuscleGroup.back, MuscleGroup.core)),
        DayTemplate("Full C", (MuscleGroup.legs, MuscleGroup.chest, MuscleGroup.back, MuscleGroup.biceps)),
    ),
    "half_split": (
        DayTemplate("Half A", (MuscleGroup.chest, MuscleGroup.back, MuscleGroup.core)),
        DayTemplate("Half B", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.shoulders)),
        DayTemplate("Half C", (MuscleGroup.back, MuscleGroup.biceps, MuscleGroup.triceps, MuscleGroup.core)),
        DayTemplate("Half D", (MuscleGroup.legs, MuscleGroup.shoulders, MuscleGroup.calves)),
    ),
    "upper_lower": (
        DayTemplate("Upper A", (MuscleGroup.chest, MuscleGroup.back, MuscleGroup.shoulders, MuscleGroup.biceps, MuscleGroup.triceps)),
        DayTemplate("Lower A", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.calves, MuscleGroup.core)),
        DayTemplate("Upper B", (MuscleGroup.back, MuscleGroup.chest, MuscleGroup.shoulders, MuscleGroup.triceps, MuscleGroup.biceps)),
        DayTemplate("Lower B", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.core, MuscleGroup.calves)),
    ),
    "split": (
        DayTemplate("Push", (MuscleGroup.chest, MuscleGroup.shoulders, MuscleGroup.triceps)),
        DayTemplate("Pull", (MuscleGroup.back, MuscleGroup.biceps, MuscleGroup.forearms)),
        DayTemplate("Legs", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.calves, MuscleGroup.core)),
        DayTemplate("Push", (MuscleGroup.chest, MuscleGroup.shoulders, MuscleGroup.triceps)),
        DayTemplate("Pull", (MuscleGroup.back, MuscleGroup.biceps)),
        DayTemplate("Legs", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.core)),
    ),
    "ppl": (
        DayTemplate("Push", (MuscleGroup.chest, MuscleGroup.shoulders, MuscleGroup.triceps)),
        DayTemplate("Pull", (MuscleGroup.back, MuscleGroup.biceps, MuscleGroup.forearms)),
        DayTemplate("Legs", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.calves, MuscleGroup.core)),
        DayTemplate("Push", (MuscleGroup.chest, MuscleGroup.shoulders, MuscleGroup.triceps)),
        DayTemplate("Pull", (MuscleGroup.back, MuscleGroup.biceps)),
        DayTemplate("Legs", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.core)),
    ),
}

STRUCTURE_ALIASES: Final[dict[str, str]] = {
    "full_body": "full_body",
    "half_split": "half_split",
    "upper_lower": "upper_lower",
    "split": "split",
    "ppl": "split",
}


def normalize_structure(value: str | None) -> str | None:
    if not value:
        return None
    key = str(value).strip().lower()
    return STRUCTURE_ALIASES.get(key)


def pick_split(
    days_per_week: int,
    experience: Experience,
    requested_structure: str | None = None,
) -> str:
    """Choose a split key, honoring user preference when feasible.

    Beginner + 2-3 days defaults to full body for safety; we still allow
    upper/lower for intermediate users at 3 days only as a half-split.
    """
    structure = normalize_structure(requested_structure)
    if structure:
        if structure == "full_body":
            return "full_body"
        if structure == "half_split":
            return "half_split" if days_per_week >= 3 else "full_body"
        if structure == "upper_lower":
            return "upper_lower" if days_per_week >= 4 else "full_body"
        if structure == "split":
            return "split" if days_per_week >= 4 else "upper_lower"

    if experience == Experience.beginner or days_per_week <= 3:
        return "full_body"
    if days_per_week == 4:
        return "upper_lower"
    return "split"
