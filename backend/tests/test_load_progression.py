from __future__ import annotations

from dataclasses import dataclass

from app.models.exercise import Equipment, ExerciseCategory, MuscleGroup
from app.models.user import Experience, Goal
from app.services.workout.load_progression import (
    LiftRecord,
    TEST_EASY_WEIGHT_FRACTION_FROM_E1RM,
    TEST_WEIGHT_FRACTION_FROM_E1RM,
    WeekKind,
    build_test_prescription,
    build_test_week_easy_prescription,
    build_working_prescription,
    double_progression_step,
    epley_one_rm,
    target_percent,
    week_kind,
)


@dataclass
class FakeExercise:
    id: int = 1
    name_ru: str = "Жим"
    primary_muscle: MuscleGroup = MuscleGroup.chest
    equipment: Equipment = Equipment.barbell
    category: ExerciseCategory = ExerciseCategory.compound
    difficulty: int = 3
    contraindications: list[str] = None
    movement_archetype: str = "bench_press_barbell"
    is_home: bool = False
    is_gym: bool = True
    suitable_for_test: bool = True
    suitable_for_progression: bool = True
    is_active: bool = True


def _ex(**overrides) -> FakeExercise:
    base = FakeExercise()
    base.contraindications = []
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_epley_increases_with_reps():
    assert epley_one_rm(100, 1) == 103.33
    assert epley_one_rm(100, 5) == 116.67
    assert epley_one_rm(100, 10) > 130.0


def test_week_kind_classification():
    assert week_kind(1) is WeekKind.test
    assert week_kind(2) is WeekKind.base
    assert week_kind(3) is WeekKind.overload
    assert week_kind(4) is WeekKind.consolidation


def test_target_percent_progression_for_strength():
    pct_test = target_percent(Goal.strength, 1)
    pct_overload = target_percent(Goal.strength, 3)
    pct_consol = target_percent(Goal.strength, 4)
    assert pct_test < pct_overload
    assert pct_consol < pct_overload


def test_test_prescription_uses_single_set_and_russian_instruction():
    prescription = build_test_prescription(_ex(), Experience.intermediate, Goal.muscle_gain)
    assert prescription.sets == 1
    assert prescription.is_test_set is True
    assert "запасом" in prescription.test_instruction or "запасе" in prescription.test_instruction
    assert "RIR" in prescription.rpe_text or "запас" in prescription.rpe_text
    assert prescription.weight_kg is not None


def test_test_prescription_target_rir_is_two_and_warmups_in_instruction():
    prescription = build_test_prescription(_ex(), Experience.intermediate, Goal.muscle_gain)
    assert prescription.target_rir == 2.0
    assert "разминоч" in prescription.test_instruction
    assert "запасом 2" in prescription.test_instruction or "RIR 2" in prescription.test_instruction
    assert "RIR 2" in prescription.rpe_text


def test_test_prescription_uses_60_percent_when_prev_e1rm_known():
    prescription = build_test_prescription(
        _ex(), Experience.intermediate, Goal.muscle_gain, prev_e1rm=120.0,
    )
    assert prescription.weight_kg is not None
    expected = 120.0 * TEST_WEIGHT_FRACTION_FROM_E1RM
    assert abs(prescription.weight_kg - expected) <= 5.0
    assert prescription.target_percent_1rm == TEST_WEIGHT_FRACTION_FROM_E1RM


def test_test_prescription_falls_back_to_starter_when_no_e1rm():
    prescription = build_test_prescription(_ex(), Experience.beginner, Goal.muscle_gain)
    assert prescription.weight_kg is not None
    assert prescription.target_percent_1rm is None


def test_test_easy_prescription_is_lighter_and_rir_three():
    prescription = build_test_week_easy_prescription(
        _ex(), Experience.intermediate, Goal.muscle_gain, prev_e1rm=120.0,
    )
    assert prescription.is_test_set is False
    assert prescription.target_rir == 3.0
    assert prescription.target_percent_1rm == TEST_EASY_WEIGHT_FRACTION_FROM_E1RM
    assert prescription.weight_kg is not None
    assert prescription.weight_kg < 120.0 * TEST_WEIGHT_FRACTION_FROM_E1RM
    assert "разминоч" in prescription.notes.lower() or "тестов" in prescription.notes.lower()


def test_test_easy_prescription_handles_bodyweight_archetype():
    bw_ex = _ex(movement_archetype="bodyweight_main", equipment=Equipment.bodyweight)
    prescription = build_test_week_easy_prescription(
        bw_ex, Experience.beginner, Goal.muscle_gain,
    )
    assert prescription.weight_kg is None
    assert prescription.target_rir == 3.0


def test_working_prescription_includes_target_rir_and_weight_for_compound():
    prescription = build_working_prescription(
        _ex(), Experience.intermediate, Goal.muscle_gain, week_index=2, estimated_1rm=100.0,
    )
    assert prescription.is_test_set is False
    assert prescription.target_rir is not None
    assert prescription.weight_kg is not None
    assert prescription.weight_kg <= 100.0
    assert prescription.target_percent_1rm is not None


def test_working_prescription_uses_starter_when_no_estimate():
    prescription = build_working_prescription(
        _ex(), Experience.beginner, Goal.muscle_gain, week_index=2, estimated_1rm=None,
    )
    assert prescription.weight_kg is not None
    assert prescription.target_percent_1rm is None


def test_consolidation_week_reduces_sets_for_non_strength_goal():
    week3 = build_working_prescription(_ex(), Experience.intermediate, Goal.muscle_gain, 3, 100.0)
    week4 = build_working_prescription(_ex(), Experience.intermediate, Goal.muscle_gain, 4, 100.0)
    assert week4.sets <= week3.sets


def test_double_progression_increases_after_success():
    record = LiftRecord(last_weight=60.0, last_reps_completed=10, last_rir=1.5, successful_streak=2)
    new_weight, msg = double_progression_step(record, "bench_press_barbell", Experience.intermediate)
    assert new_weight == 62.5
    assert "прогрессия" in msg.lower() or "плит" in msg.lower()


def test_double_progression_deloads_after_failure():
    record = LiftRecord(last_weight=80.0, last_reps_completed=4, last_rir=0.0, successful_streak=0)
    new_weight, msg = double_progression_step(record, "bench_press_barbell", Experience.intermediate)
    assert new_weight is not None and new_weight < 80.0
    assert "Дроп" in msg or "−5" in msg


def test_double_progression_holds_when_partial():
    record = LiftRecord(last_weight=70.0, last_reps_completed=8, last_rir=2.0, successful_streak=0)
    new_weight, msg = double_progression_step(record, "bench_press_barbell", Experience.intermediate)
    assert new_weight == 70.0
    assert "удержив" in msg.lower() or "повтор" in msg.lower()


def test_double_progression_returns_starter_when_no_history():
    record = LiftRecord()
    new_weight, msg = double_progression_step(record, "bench_press_barbell", Experience.beginner)
    assert new_weight is not None and new_weight > 0
    assert "стартов" in msg.lower()


def test_double_progression_skips_bodyweight():
    record = LiftRecord(last_weight=None, last_reps_completed=10)
    new_weight, msg = double_progression_step(record, "bodyweight_main", Experience.intermediate)
    assert new_weight is None
    assert "технике" in msg.lower() or "повтор" in msg.lower()
