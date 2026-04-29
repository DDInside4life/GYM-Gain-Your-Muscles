"""Inter-mesocycle progression.

When a user starts a new mesocycle, we:
1. Compute the best e1RM from the last cycle's SetLog (max of old stored e1RM
   and the best logged Epley with RIR correction).
2. Apply double-progression to each exercise: +plate if RIR ≥ 1, −5 % if
   RIR = 0, hold otherwise.
3. Set test-week starter weight to 65 % of the new e1RM (up from 60 % on the
   first mesocycle since technique has been validated).
4. Auto-insert deload weeks according to cycle_length_weeks:
   - Every 4th week is a deload (emergent / default rule)
   - The caller (WorkoutGenerator) already handles deload via
     week_modifier(emergent / block) — here we just annotate the cycle
     metadata so the UI can show "Deload" badges.

This service does NOT write to the DB directly; it returns a
``NextCycleContext`` that ``WorkoutGenerator.generate_from_context`` consumes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import SetLog
from app.services.workout.auto_weights import adjusted_e1rm
from app.services.workout.load_progression import (
    LiftRecord,
    double_progression_step,
)
from app.models.user import Experience, Goal


SECOND_CYCLE_TEST_FRACTION: float = 0.65
FIRST_CYCLE_TEST_FRACTION: float = 0.60


@dataclass(slots=True)
class ExerciseProgression:
    exercise_id: int
    prev_e1rm: float
    new_e1rm: float
    suggested_weight: float | None
    note: str


@dataclass(slots=True)
class NextCycleContext:
    cycle_number: int
    test_weight_fraction: float
    progressions: dict[int, ExerciseProgression] = field(default_factory=dict)
    deload_weeks: list[int] = field(default_factory=list)


def deload_week_indices(total_weeks: int) -> list[int]:
    """Return 1-based week indices that should be deload weeks."""
    if total_weeks <= 3:
        return []
    indices: list[int] = []
    w = 4
    while w <= total_weeks:
        indices.append(w)
        w += 4
    if total_weeks not in indices and total_weeks >= 4:
        indices.append(total_weeks)
    return sorted(set(indices))


async def build_next_cycle_context(
    db: AsyncSession,
    user_id: int,
    plan_id: int,
    cycle_number: int,
    experience: Experience,
    goal: Goal,
) -> NextCycleContext:
    """Aggregate last-cycle data and compute per-exercise progressions."""
    is_second_cycle_or_later = cycle_number > 1
    test_fraction = (
        SECOND_CYCLE_TEST_FRACTION if is_second_cycle_or_later else FIRST_CYCLE_TEST_FRACTION
    )

    stmt = (
        select(SetLog)
        .where(SetLog.plan_id == plan_id, SetLog.user_id == user_id)
        .order_by(SetLog.exercise_id, SetLog.set_index)
    )
    logs = (await db.execute(stmt)).scalars().all()

    agg: dict[int, LiftRecord] = {}
    for log in logs:
        prev = agg.get(log.exercise_id, LiftRecord())
        cur_e1rm = adjusted_e1rm(log.completed_weight_kg, log.completed_reps, log.rir or 0.0)
        best_e1rm = max(prev.estimated_1rm or 0.0, log.estimated_1rm or 0.0, cur_e1rm)
        streak = prev.successful_streak + (1 if log.rir is not None and log.rir >= 1.0 else 0)
        agg[log.exercise_id] = LiftRecord(
            estimated_1rm=best_e1rm,
            last_weight=log.completed_weight_kg,
            last_reps_completed=log.completed_reps,
            last_rir=log.rir,
            successful_streak=streak,
        )

    progressions: dict[int, ExerciseProgression] = {}
    for exercise_id, record in agg.items():
        ex_archetype = "generic"
        new_weight, note = double_progression_step(record, ex_archetype, experience)
        progressions[exercise_id] = ExerciseProgression(
            exercise_id=exercise_id,
            prev_e1rm=record.estimated_1rm or 0.0,
            new_e1rm=record.estimated_1rm or 0.0,
            suggested_weight=new_weight,
            note=note,
        )

    return NextCycleContext(
        cycle_number=cycle_number,
        test_weight_fraction=test_fraction,
        progressions=progressions,
    )
