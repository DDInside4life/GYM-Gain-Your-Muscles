"""Volume budgeting: per-day, per-muscle, weekly caps."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.models.exercise import Exercise, ExerciseCategory, MuscleGroup
from app.models.user import Experience, Goal


MIN_EXERCISES_PER_DAY: Final[int] = 4
ABSOLUTE_MAX_EXERCISES_PER_DAY: Final[int] = 7
MAX_SETS_PER_MUSCLE_PER_SESSION: Final[int] = 12


@dataclass(frozen=True, slots=True)
class GoalVolume:
    max_exercises_per_day: int
    max_sets_per_muscle_session: int
    sets_per_compound: int
    sets_per_isolation: int
    reps_min_compound: int
    reps_max_compound: int
    reps_min_isolation: int
    reps_max_isolation: int
    rest_compound_sec: int
    rest_isolation_sec: int
    target_rir_compound: float
    target_rir_isolation: float
    volume_factor: float


GOAL_VOLUME: Final[dict[Goal, GoalVolume]] = {
    Goal.strength: GoalVolume(
        max_exercises_per_day=5, max_sets_per_muscle_session=8,
        sets_per_compound=5, sets_per_isolation=3,
        reps_min_compound=3, reps_max_compound=6,
        reps_min_isolation=6, reps_max_isolation=10,
        rest_compound_sec=210, rest_isolation_sec=120,
        target_rir_compound=1.0, target_rir_isolation=1.0,
        volume_factor=0.40,
    ),
    Goal.muscle_gain: GoalVolume(
        max_exercises_per_day=6, max_sets_per_muscle_session=12,
        sets_per_compound=4, sets_per_isolation=3,
        reps_min_compound=6, reps_max_compound=10,
        reps_min_isolation=10, reps_max_isolation=14,
        rest_compound_sec=120, rest_isolation_sec=75,
        target_rir_compound=2.0, target_rir_isolation=1.0,
        volume_factor=0.55,
    ),
    Goal.fat_loss: GoalVolume(
        max_exercises_per_day=7, max_sets_per_muscle_session=10,
        sets_per_compound=3, sets_per_isolation=3,
        reps_min_compound=8, reps_max_compound=12,
        reps_min_isolation=12, reps_max_isolation=18,
        rest_compound_sec=75, rest_isolation_sec=45,
        target_rir_compound=2.0, target_rir_isolation=2.0,
        volume_factor=0.45,
    ),
    Goal.endurance: GoalVolume(
        max_exercises_per_day=6, max_sets_per_muscle_session=10,
        sets_per_compound=3, sets_per_isolation=3,
        reps_min_compound=10, reps_max_compound=15,
        reps_min_isolation=15, reps_max_isolation=20,
        rest_compound_sec=60, rest_isolation_sec=40,
        target_rir_compound=2.0, target_rir_isolation=2.0,
        volume_factor=0.40,
    ),
    Goal.general: GoalVolume(
        max_exercises_per_day=5, max_sets_per_muscle_session=8,
        sets_per_compound=3, sets_per_isolation=3,
        reps_min_compound=6, reps_max_compound=10,
        reps_min_isolation=10, reps_max_isolation=14,
        rest_compound_sec=90, rest_isolation_sec=60,
        target_rir_compound=2.0, target_rir_isolation=2.0,
        volume_factor=0.42,
    ),
}


WEEKLY_SETS_PER_MUSCLE: Final[dict[Experience, int]] = {
    Experience.beginner:     10,
    Experience.intermediate: 16,
    Experience.advanced:     22,
}


def goal_volume(goal: Goal) -> GoalVolume:
    return GOAL_VOLUME.get(goal, GOAL_VOLUME[Goal.general])


def weekly_cap(experience: Experience) -> int:
    return WEEKLY_SETS_PER_MUSCLE[experience]


def sets_for(exercise: Exercise, goal: Goal) -> int:
    cfg = goal_volume(goal)
    if exercise.category == ExerciseCategory.compound:
        return cfg.sets_per_compound
    return cfg.sets_per_isolation


@dataclass(slots=True)
class WeeklyMuscleBudget:
    """Tracks remaining weekly sets per primary muscle group."""

    cap: int
    used: dict[MuscleGroup, int]

    @classmethod
    def for_experience(cls, experience: Experience) -> "WeeklyMuscleBudget":
        return cls(cap=weekly_cap(experience), used={})

    def remaining(self, muscle: MuscleGroup) -> int:
        return max(0, self.cap - self.used.get(muscle, 0))

    def can_add(self, muscle: MuscleGroup, sets: int) -> bool:
        return self.remaining(muscle) >= sets

    def add(self, muscle: MuscleGroup, sets: int) -> None:
        self.used[muscle] = self.used.get(muscle, 0) + sets
