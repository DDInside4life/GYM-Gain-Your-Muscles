"""CRITICAL BUG ZONE: equipment=['bodyweight'] must yield only bodyweight."""
from __future__ import annotations

from dataclasses import dataclass

from app.models.exercise import Equipment, ExerciseCategory, MuscleGroup
from app.models.user import Experience
from app.services.workout.filtering import FilterCriteria, filter_pool


@dataclass
class FakeExercise:
    id: int
    name_ru: str
    primary_muscle: MuscleGroup
    equipment: Equipment
    category: ExerciseCategory
    difficulty: int
    contraindications: list[str]
    movement_archetype: str = "generic"
    is_home: bool = True
    is_gym: bool = True
    suitable_for_test: bool = False
    suitable_for_progression: bool = True
    is_active: bool = True


def _diverse_pool() -> list[FakeExercise]:
    return [
        FakeExercise(1, "Отжимания", MuscleGroup.chest, Equipment.bodyweight,
                     ExerciseCategory.compound, 1, [], "bodyweight_main"),
        FakeExercise(2, "Приседания", MuscleGroup.legs, Equipment.bodyweight,
                     ExerciseCategory.compound, 2, [], "bodyweight_main"),
        FakeExercise(3, "Жим штанги", MuscleGroup.chest, Equipment.barbell,
                     ExerciseCategory.compound, 3, [], "bench_press_barbell"),
        FakeExercise(4, "Тяга гантели", MuscleGroup.back, Equipment.dumbbell,
                     ExerciseCategory.compound, 2, [], "dumbbell_compound"),
        FakeExercise(5, "Жим в тренажёре", MuscleGroup.chest, Equipment.machine,
                     ExerciseCategory.isolation, 1, [], "machine"),
        FakeExercise(6, "Тяга в кроссовере", MuscleGroup.back, Equipment.cable,
                     ExerciseCategory.isolation, 2, [], "cable"),
        FakeExercise(7, "Гири жим", MuscleGroup.shoulders, Equipment.kettlebell,
                     ExerciseCategory.compound, 2, [], "kettlebell"),
        FakeExercise(8, "Резина", MuscleGroup.back, Equipment.bands,
                     ExerciseCategory.isolation, 1, [], "bands"),
    ]


def test_bodyweight_only_yields_only_bodyweight() -> None:
    """equipment={bodyweight} STRICT RULE: ZERO non-bodyweight exits the filter."""
    pool = _diverse_pool()
    criteria = FilterCriteria(
        location="home",
        equipment=frozenset({Equipment.bodyweight}),
        contraindications=frozenset(),
        experience=Experience.intermediate,
    )
    result = filter_pool(pool, criteria)
    assert result, "expected bodyweight pool to be non-empty"
    leaks = [ex for ex in result if ex.equipment != Equipment.bodyweight]
    assert not leaks, f"non-bodyweight leaked into result: {[ex.name_ru for ex in leaks]}"


def test_empty_equipment_set_means_no_filtering() -> None:
    pool = _diverse_pool()
    criteria = FilterCriteria(
        location="gym",
        equipment=frozenset(),
        contraindications=frozenset(),
        experience=Experience.advanced,
    )
    result = filter_pool(pool, criteria)
    assert {ex.equipment for ex in result} >= {
        Equipment.bodyweight, Equipment.barbell, Equipment.dumbbell,
    }


def test_bodyweight_plus_dumbbell_excludes_barbell_and_machines() -> None:
    pool = _diverse_pool()
    criteria = FilterCriteria(
        location="home",
        equipment=frozenset({Equipment.bodyweight, Equipment.dumbbell}),
        contraindications=frozenset(),
        experience=Experience.intermediate,
    )
    result = filter_pool(pool, criteria)
    assert {ex.equipment for ex in result} <= {Equipment.bodyweight, Equipment.dumbbell}


def test_inactive_exercises_always_excluded() -> None:
    pool = _diverse_pool()
    pool[0].is_active = False
    criteria = FilterCriteria(
        location="home",
        equipment=frozenset({Equipment.bodyweight}),
        contraindications=frozenset(),
        experience=Experience.intermediate,
    )
    result = filter_pool(pool, criteria)
    assert all(ex.is_active for ex in result)


def test_knee_injury_strips_high_impact_and_deep_squat() -> None:
    pool = _diverse_pool() + [
        FakeExercise(9, "Глубокий присед", MuscleGroup.legs, Equipment.barbell,
                     ExerciseCategory.compound, 4, ["deep_squat", "knee"], "back_squat_barbell"),
        FakeExercise(10, "Прыжки", MuscleGroup.legs, Equipment.bodyweight,
                     ExerciseCategory.cardio, 2, ["high_impact"], "plyo"),
    ]
    from app.services.workout.filtering import resolve_contraindications
    criteria = FilterCriteria(
        location="gym",
        equipment=frozenset({Equipment.barbell, Equipment.bodyweight}),
        contraindications=resolve_contraindications(["knees"]),
        experience=Experience.advanced,
    )
    result = filter_pool(pool, criteria)
    assert all("deep_squat" not in (ex.contraindications or []) for ex in result)
    assert all("high_impact" not in (ex.contraindications or []) for ex in result)
