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
    "upper_lower": (
        DayTemplate("Upper A", (MuscleGroup.chest, MuscleGroup.back, MuscleGroup.shoulders, MuscleGroup.biceps, MuscleGroup.triceps)),
        DayTemplate("Lower A", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.calves, MuscleGroup.core)),
        DayTemplate("Upper B", (MuscleGroup.back, MuscleGroup.chest, MuscleGroup.shoulders, MuscleGroup.triceps, MuscleGroup.biceps)),
        DayTemplate("Lower B", (MuscleGroup.legs, MuscleGroup.glutes, MuscleGroup.core, MuscleGroup.calves)),
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


def pick_split(days_per_week: int, experience: Experience) -> str:
    if experience == Experience.beginner or days_per_week <= 3:
        return "full_body"
    if days_per_week == 4:
        return "upper_lower"
    return "ppl"
