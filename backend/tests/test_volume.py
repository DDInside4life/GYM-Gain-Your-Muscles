from __future__ import annotations

from app.models.exercise import MuscleGroup
from app.models.user import Experience, Goal
from app.services.workout.volume import (
    GOAL_VOLUME,
    WeeklyMuscleBudget,
    goal_volume,
    weekly_cap,
)


def test_goal_volume_caps_match_design():
    assert goal_volume(Goal.strength).max_exercises_per_day == 5
    assert goal_volume(Goal.muscle_gain).max_exercises_per_day == 6
    assert goal_volume(Goal.fat_loss).max_exercises_per_day == 7
    for cfg in GOAL_VOLUME.values():
        assert cfg.max_sets_per_muscle_session <= 12


def test_weekly_cap_increases_with_experience():
    assert weekly_cap(Experience.beginner) < weekly_cap(Experience.intermediate)
    assert weekly_cap(Experience.intermediate) < weekly_cap(Experience.advanced)


def test_weekly_budget_can_add_until_cap():
    budget = WeeklyMuscleBudget.for_experience(Experience.intermediate)
    cap = weekly_cap(Experience.intermediate)
    assert budget.can_add(MuscleGroup.chest, 4)
    budget.add(MuscleGroup.chest, cap)
    assert not budget.can_add(MuscleGroup.chest, 1)
    assert budget.remaining(MuscleGroup.chest) == 0
    assert budget.remaining(MuscleGroup.back) == cap


def test_target_rir_present_for_every_goal():
    for cfg in GOAL_VOLUME.values():
        assert cfg.target_rir_compound >= 1.0
        assert cfg.target_rir_isolation >= 1.0
