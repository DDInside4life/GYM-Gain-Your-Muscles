"""Production-grade load progression: combined %1RM + volume budget.

This module is pure math. It does not access the database.

Inputs come from the test result, the recent log history, the goal, and the
volume budget. Outputs are concrete (sets, reps, weight, rest, RIR, RPE text,
notes) ready to persist.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from app.models.exercise import Exercise, ExerciseCategory
from app.models.user import Experience, Goal
from app.services.workout.starter_weights import (
    clamp_to_safety,
    plate_for,
    round_to_plate,
    starter_weight,
)
from app.services.workout.volume import GoalVolume, goal_volume


class WeekKind(str, Enum):
    test = "test"
    base = "base"
    overload = "overload"
    consolidation = "consolidation"


WEEK_KIND_BY_INDEX: Final[dict[int, WeekKind]] = {
    1: WeekKind.test,
    2: WeekKind.base,
    3: WeekKind.overload,
    4: WeekKind.consolidation,
}


# Goal × week-kind → percent of estimated 1RM
TARGET_PERCENT: Final[dict[Goal, dict[WeekKind, float]]] = {
    Goal.strength: {
        WeekKind.test: 0.65, WeekKind.base: 0.75,
        WeekKind.overload: 0.825, WeekKind.consolidation: 0.775,
    },
    Goal.muscle_gain: {
        WeekKind.test: 0.60, WeekKind.base: 0.675,
        WeekKind.overload: 0.725, WeekKind.consolidation: 0.70,
    },
    Goal.fat_loss: {
        WeekKind.test: 0.50, WeekKind.base: 0.60,
        WeekKind.overload: 0.65, WeekKind.consolidation: 0.625,
    },
    Goal.endurance: {
        WeekKind.test: 0.45, WeekKind.base: 0.55,
        WeekKind.overload: 0.60, WeekKind.consolidation: 0.55,
    },
    Goal.general: {
        WeekKind.test: 0.55, WeekKind.base: 0.625,
        WeekKind.overload: 0.675, WeekKind.consolidation: 0.65,
    },
}


@dataclass(frozen=True, slots=True)
class LiftRecord:
    """Aggregated history for one exercise/user used for next-month rebuild."""

    estimated_1rm: float | None = None
    successful_streak: int = 0
    last_weight: float | None = None
    last_reps_completed: int | None = None
    last_rir: float | None = None


@dataclass(frozen=True, slots=True)
class Prescription:
    sets: int
    reps_min: int
    reps_max: int
    rest_sec: int
    weight_kg: float | None
    target_percent_1rm: float | None
    target_rir: float | None
    rpe_text: str
    is_test_set: bool
    test_instruction: str
    notes: str


def epley_one_rm(weight: float, reps: int) -> float:
    if reps <= 0:
        return 0.0
    return round(weight * (1 + reps / 30.0), 2)


def week_kind(week_index: int) -> WeekKind:
    return WEEK_KIND_BY_INDEX.get(week_index, WeekKind.base)


def target_percent(goal: Goal, week_index: int) -> float:
    table = TARGET_PERCENT.get(goal, TARGET_PERCENT[Goal.general])
    return table.get(week_kind(week_index), 0.65)


def _rpe_text(rir: float, kind: WeekKind, category: ExerciseCategory) -> str:
    if kind == WeekKind.test:
        return "Тестовый подход. Оставьте 1–2 повтора в запасе, не до отказа."
    if rir <= 1.0:
        return "Тяжёлый подход. RIR 1: оставьте 1 повтор в запасе."
    if rir <= 2.0:
        return "Рабочая интенсивность. RIR 2: оставьте 2 повтора в запасе."
    return "Контроль техники. RIR 2–3: запас 2–3 повтора."


def _notes_for_week(kind: WeekKind, week_index: int) -> str:
    if kind == WeekKind.test:
        return "Тестовая неделя. Один рабочий подход на упражнение."
    if kind == WeekKind.base:
        return f"Неделя {week_index}: базовая нагрузка по результатам теста."
    if kind == WeekKind.overload:
        return f"Неделя {week_index}: прогрессирующая перегрузка."
    return f"Неделя {week_index}: консолидация и контроль усталости."


def _volume_weight(
    estimated_1rm: float,
    sets: int,
    reps_avg: float,
    cfg: GoalVolume,
) -> float:
    if sets <= 0 or reps_avg <= 0:
        return 0.0
    tonnage_budget = cfg.volume_factor * estimated_1rm * sets * reps_avg
    return tonnage_budget / (sets * reps_avg)


def build_test_prescription(
    exercise: Exercise,
    experience: Experience,
    goal: Goal,
) -> Prescription:
    cfg = goal_volume(goal)
    is_compound = exercise.category == ExerciseCategory.compound
    reps_min = cfg.reps_min_compound if is_compound else cfg.reps_min_isolation
    reps_max = cfg.reps_max_compound if is_compound else cfg.reps_max_isolation
    if exercise.equipment.value == "bodyweight":
        reps_max = max(reps_max, 15)
    weight = starter_weight(exercise.movement_archetype, experience, goal)
    return Prescription(
        sets=1,
        reps_min=max(3, reps_min - 1),
        reps_max=min(20, reps_max + 2),
        rest_sec=cfg.rest_compound_sec if is_compound else cfg.rest_isolation_sec,
        weight_kg=weight,
        target_percent_1rm=None,
        target_rir=1.0,
        rpe_text=_rpe_text(1.0, WeekKind.test, exercise.category),
        is_test_set=True,
        test_instruction=(
            "Один рабочий подход с запасом 1–2 повтора. Не доводите до отказа, "
            "сохраняйте чистую технику. Сохраните вес и количество повторений."
        ),
        notes=_notes_for_week(WeekKind.test, 1),
    )


def build_working_prescription(
    exercise: Exercise,
    experience: Experience,
    goal: Goal,
    week_index: int,
    estimated_1rm: float | None,
) -> Prescription:
    cfg = goal_volume(goal)
    is_compound = exercise.category == ExerciseCategory.compound
    sets = cfg.sets_per_compound if is_compound else cfg.sets_per_isolation
    if week_index == 4:
        sets = max(2, sets - 1)
    reps_min = cfg.reps_min_compound if is_compound else cfg.reps_min_isolation
    reps_max = cfg.reps_max_compound if is_compound else cfg.reps_max_isolation
    rest = cfg.rest_compound_sec if is_compound else cfg.rest_isolation_sec
    rir = cfg.target_rir_compound if is_compound else cfg.target_rir_isolation
    kind = week_kind(week_index)

    weight: float | None = None
    pct: float | None = None
    if estimated_1rm and exercise.movement_archetype not in {"bodyweight_main", "cardio"}:
        pct = target_percent(goal, week_index)
        intensity_weight = estimated_1rm * pct
        reps_avg = (reps_min + reps_max) / 2.0
        volume_weight = _volume_weight(estimated_1rm, sets, reps_avg, cfg)
        chosen = min(intensity_weight, volume_weight) if volume_weight > 0 else intensity_weight
        archetype_plate = plate_for(exercise.movement_archetype)
        weight = clamp_to_safety(
            exercise.movement_archetype, experience, round_to_plate(chosen, archetype_plate),
        )
    elif exercise.movement_archetype not in {"bodyweight_main", "cardio"}:
        weight = starter_weight(exercise.movement_archetype, experience, goal)

    return Prescription(
        sets=sets,
        reps_min=reps_min,
        reps_max=reps_max,
        rest_sec=rest,
        weight_kg=weight,
        target_percent_1rm=pct,
        target_rir=rir,
        rpe_text=_rpe_text(rir, kind, exercise.category),
        is_test_set=False,
        test_instruction="",
        notes=_notes_for_week(kind, week_index),
    )


def double_progression_step(
    record: LiftRecord,
    archetype: str,
    experience: Experience,
) -> tuple[float | None, str]:
    """Apply double-progression rules to a stored lift record.

    Returns the suggested next weight (kg) and a Russian explanation. ``None``
    is returned for bodyweight/cardio archetypes.
    """
    if archetype in {"bodyweight_main", "cardio"}:
        return None, "Прогрессия по технике и количеству повторений."
    plate = plate_for(archetype)
    if record.last_weight is None:
        starter = starter_weight(archetype, experience, Goal.general)
        return starter, "Используется стартовая нагрузка из таблицы."

    success = (
        record.successful_streak >= 1
        and record.last_rir is not None
        and record.last_rir >= 1.0
    )
    failure = record.last_rir is not None and record.last_rir <= 0.0

    if failure:
        new_weight = clamp_to_safety(archetype, experience, record.last_weight * 0.95)
        return round_to_plate(new_weight, plate), "Дроп −5%: техника или RIR=0 на прошлой сессии."
    if success:
        new_weight = clamp_to_safety(archetype, experience, record.last_weight + plate)
        return new_weight, "Двойная прогрессия: рост на минимальный шаг плит."
    return record.last_weight, "Удерживаем вес: цель — добрать повторения."


def estimated_1rm_from_record(record: LiftRecord) -> float | None:
    if record.estimated_1rm and record.estimated_1rm > 0:
        return record.estimated_1rm
    if record.last_weight and record.last_reps_completed:
        return epley_one_rm(record.last_weight, record.last_reps_completed)
    return None
