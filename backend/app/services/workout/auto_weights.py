"""Automatic weight calculation after the test week.

Pure math service: reads test-week SetLog rows, computes adjusted e1RM via
Epley with RIR correction, then translates each exercise's e1RM into a
concrete working weight for every subsequent week of the mesocycle.

Formula
-------
    adjusted_reps = completed_reps + rir
    e1rm           = weight × (1 + adjusted_reps / 30)

    working_weight = round_to_plate(
        min(e1rm × TARGET_PERCENT[goal][week_kind],
            volume_weight_cap(e1rm, sets, reps_avg, cfg)),
    )
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise, ExerciseCategory
from app.models.user import Experience, Goal
from app.models.workout import SetLog, WorkoutDay, WorkoutExercise, WorkoutPlan
from app.services.workout.load_progression import (
    TARGET_PERCENT,
    WeekKind,
    week_kind,
)
from app.services.workout.starter_weights import (
    clamp_to_safety,
    plate_for,
    round_to_plate,
)
from app.services.workout.volume import goal_volume

MIN_RIR_VALID: Final[float] = 0.0
MAX_RIR_VALID: Final[float] = 5.0
MIN_REPS_VALID: Final[int] = 1
MAX_REPS_VALID: Final[int] = 30


@dataclass(frozen=True, slots=True)
class ExerciseWeightResult:
    exercise_id: int
    workout_exercise_id: int
    e1rm: float
    weight_kg: float
    target_percent: float
    week_index: int


def adjusted_e1rm(weight: float, reps: int, rir: float) -> float:
    """Epley formula with RIR correction: rir reps are 'available but unused'."""
    rir_clamped = max(MIN_RIR_VALID, min(MAX_RIR_VALID, rir))
    effective_reps = reps + rir_clamped
    return round(weight * (1 + effective_reps / 30.0), 2)


def _volume_cap(e1rm: float, sets: int, reps_avg: float, volume_factor: float) -> float:
    if sets <= 0 or reps_avg <= 0:
        return e1rm
    tonnage_budget = volume_factor * e1rm * sets * reps_avg
    return tonnage_budget / (sets * reps_avg)


def _working_weight_for_week(
    e1rm: float,
    week_idx: int,
    goal: Goal,
    experience: Experience,
    archetype: str,
    sets: int,
    reps_min: int,
    reps_max: int,
) -> tuple[float, float]:
    """Return (working_weight, target_percent) for a given week."""
    table = TARGET_PERCENT.get(goal, TARGET_PERCENT[Goal.general])
    kind = week_kind(week_idx)
    pct = table.get(kind, table.get(WeekKind.base, 0.675))
    cfg = goal_volume(goal)
    reps_avg = (reps_min + reps_max) / 2.0
    intensity_w = e1rm * pct
    volume_w = _volume_cap(e1rm, sets, reps_avg, cfg.volume_factor)
    raw = min(intensity_w, volume_w) if volume_w > 0 else intensity_w
    plate = plate_for(archetype)
    weight = clamp_to_safety(archetype, experience, round_to_plate(raw, plate))
    return weight, pct


class AutoWeightCalculator:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def best_e1rm_from_test_week(
        self,
        plan_id: int,
    ) -> dict[int, tuple[float, float]]:
        """Return {exercise_id: (best_adjusted_e1rm, best_weight)} from test-week logs."""
        stmt = (
            select(SetLog)
            .where(SetLog.plan_id == plan_id, SetLog.week_index == 1)
        )
        rows = (await self.db.execute(stmt)).scalars().all()

        best: dict[int, tuple[float, float]] = {}
        for row in rows:
            if not (
                MIN_REPS_VALID <= row.completed_reps <= MAX_REPS_VALID
                and row.completed_weight_kg > 0
            ):
                continue
            rir = row.rir if row.rir is not None else 0.0
            e1rm = adjusted_e1rm(row.completed_weight_kg, row.completed_reps, rir)
            prev_e1rm, _ = best.get(row.exercise_id, (0.0, 0.0))
            if e1rm > prev_e1rm:
                best[row.exercise_id] = (e1rm, row.completed_weight_kg)
        return best

    async def recalculate_working_weeks(
        self,
        plan: WorkoutPlan,
        goal: Goal,
        experience: Experience,
    ) -> list[ExerciseWeightResult]:
        """Rewrite weight_kg / target_percent_1rm / target_rir / rpe_text for weeks 2..N."""
        e1rm_map = await self.best_e1rm_from_test_week(plan.id)

        stmt = (
            select(
                WorkoutExercise,
                WorkoutDay.week_index,
                Exercise.movement_archetype,
                Exercise.category,
            )
            .join(WorkoutDay, WorkoutDay.id == WorkoutExercise.day_id)
            .join(Exercise, Exercise.id == WorkoutExercise.exercise_id)
            .where(
                WorkoutDay.plan_id == plan.id,
                WorkoutDay.week_index > 1,
                WorkoutDay.is_rest.is_(False),
            )
            .order_by(WorkoutDay.week_index, WorkoutExercise.position)
        )
        rows = (await self.db.execute(stmt)).all()

        results: list[ExerciseWeightResult] = []
        for we, week_idx, movement_archetype, category in rows:
            e1rm, _ = e1rm_map.get(we.exercise_id, (0.0, 0.0))
            if e1rm <= 0:
                continue

            weight, pct = _working_weight_for_week(
                e1rm=e1rm,
                week_idx=week_idx,
                goal=goal,
                experience=experience,
                archetype=movement_archetype or "generic",
                sets=we.sets,
                reps_min=we.reps_min,
                reps_max=we.reps_max,
            )

            cfg = goal_volume(goal)
            rir = cfg.target_rir_compound if category == ExerciseCategory.compound else cfg.target_rir_isolation

            we.weight_kg = weight
            we.target_percent_1rm = pct
            we.target_rir = rir
            we.rpe_text = _rir_to_rpe_text(rir)

            results.append(ExerciseWeightResult(
                exercise_id=we.exercise_id,
                workout_exercise_id=we.id,
                e1rm=e1rm,
                weight_kg=weight,
                target_percent=pct,
                week_index=week_idx,
            ))

        return results


def _rir_to_rpe_text(rir: float) -> str:
    if rir <= 1.0:
        return "Тяжёлый подход. RIR 1: оставьте 1 повтор в запасе."
    if rir <= 2.0:
        return "Рабочая интенсивность. RIR 2: оставьте 2 повтора в запасе."
    return "Контроль техники. RIR 2–3: запас 2–3 повтора."
