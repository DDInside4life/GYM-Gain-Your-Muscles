from __future__ import annotations

from dataclasses import dataclass

from app.models.exercise import Equipment, ExerciseCategory, MuscleGroup
from app.models.user import Experience
from app.services.workout.filtering import (
    FilterCriteria,
    filter_pool,
    is_safe,
    matches_equipment,
    matches_location,
    resolve_contraindications,
)


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


def make_pool() -> list[FakeExercise]:
    return [
        FakeExercise(1, "Жим штанги лёжа", MuscleGroup.chest, Equipment.barbell, ExerciseCategory.compound, 3,
                     ["bench_heavy"], "bench_press_barbell", is_home=False, suitable_for_test=True),
        FakeExercise(2, "Отжимания", MuscleGroup.chest, Equipment.bodyweight, ExerciseCategory.compound, 1,
                     [], "bodyweight_main"),
        FakeExercise(3, "Становая тяга", MuscleGroup.back, Equipment.barbell, ExerciseCategory.compound, 5,
                     ["heavy_deadlift", "spine_load"], "deadlift_barbell", is_home=False, suitable_for_test=True),
        FakeExercise(4, "Тяга в наклоне", MuscleGroup.back, Equipment.dumbbell, ExerciseCategory.compound, 2,
                     [], "dumbbell_compound"),
    ]


def test_resolve_contraindications_unique_tokens():
    tokens = resolve_contraindications(["Knee", "back", "unknown"])
    assert "knee" in tokens
    assert "spine_load" in tokens
    assert "unknown" not in tokens


def test_is_safe_excludes_matching_contras():
    pool = make_pool()
    contras = resolve_contraindications(["back"])
    assert not is_safe(pool[2], contras)
    assert is_safe(pool[1], contras)


def test_matches_location_home_filters_gym_only():
    bench = FakeExercise(1, "Жим", MuscleGroup.chest, Equipment.barbell,
                         ExerciseCategory.compound, 3, [], is_home=False)
    assert matches_location(bench, "gym")
    assert not matches_location(bench, "home")


def test_matches_equipment_respects_available_set():
    bench = FakeExercise(1, "Жим", MuscleGroup.chest, Equipment.barbell, ExerciseCategory.compound, 3, [])
    assert matches_equipment(bench, frozenset({Equipment.barbell}))
    assert not matches_equipment(bench, frozenset({Equipment.bodyweight}))


def test_filter_pool_combines_all_rules():
    pool = make_pool()
    criteria = FilterCriteria(
        location="home",
        equipment=frozenset({Equipment.bodyweight, Equipment.dumbbell}),
        contraindications=resolve_contraindications(["back"]),
        experience=Experience.beginner,
    )
    result = filter_pool(pool, criteria)
    ids = {ex.id for ex in result}
    assert 1 not in ids  # gym only
    assert 3 not in ids  # contraindicated and gym only
    assert 2 in ids
    assert 4 in ids


def test_filter_pool_respects_difficulty_cap_for_beginners():
    pool = make_pool()
    criteria = FilterCriteria(
        location="gym",
        equipment=frozenset({Equipment.barbell, Equipment.dumbbell, Equipment.bodyweight}),
        contraindications=frozenset(),
        experience=Experience.beginner,
    )
    result = filter_pool(pool, criteria)
    ids = {ex.id for ex in result}
    assert 3 not in ids


def test_filter_pool_can_require_test_set_suitability():
    pool = make_pool()
    criteria = FilterCriteria(
        location="gym",
        equipment=frozenset({Equipment.barbell, Equipment.bodyweight, Equipment.dumbbell}),
        contraindications=frozenset(),
        experience=Experience.advanced,
        require_test=True,
    )
    result = filter_pool(pool, criteria)
    ids = {ex.id for ex in result}
    assert ids <= {1, 3}
