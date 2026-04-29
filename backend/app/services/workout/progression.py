from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequest, NotFound
from app.models.workout import SetLog
from app.models.user import User
from app.models.workout import (
    Difficulty, WorkoutDay, WorkoutExercise, WorkoutFeedback, WorkoutPlan,
)
from app.repositories.workout import SetLogRepository, WorkoutFeedbackRepository, WorkoutPlanRepository
from app.services.workout.rules import (
    DELOAD_EVERY_WEEKS, DIFFICULTY_INTENSITY_MULT, DIFFICULTY_SETS_DELTA,
    AutoDeloadDecision, ComplianceAdjustment, clamp_sets, compliance_adjustment, decide_auto_deload, round_to_plate,
)


@dataclass(slots=True)
class _DayAdjustment:
    intensity_mult: float
    sets_delta: int
    skip_contras: frozenset[str]


class ProgressionService:
    """Progressive overload engine.

    Produces next week's plan from current plan + feedback. Deterministic:
    only last feedback per (day,user) matters thanks to the unique constraint.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.plans = WorkoutPlanRepository(db)
        self.feedback = WorkoutFeedbackRepository(db)
        self.set_logs = SetLogRepository(db)

    @staticmethod
    def _is_deload_week(week: int) -> bool:
        return week > 0 and week % DELOAD_EVERY_WEEKS == 0

    def _compute_adjustment(
        self,
        fb: WorkoutFeedback | None,
        discomfort_tokens: frozenset[str],
        compliance: ComplianceAdjustment,
    ) -> _DayAdjustment:
        if fb is None:
            return _DayAdjustment(min(1.0, compliance.intensity_cap), compliance.sets_delta, discomfort_tokens)
        mult = DIFFICULTY_INTENSITY_MULT[fb.difficulty]
        sets_delta = DIFFICULTY_SETS_DELTA[fb.difficulty]
        if not fb.completed:
            mult = min(mult, 0.95)
            sets_delta = min(sets_delta, 0)
        mult = min(mult, compliance.intensity_cap)
        sets_delta = max(-2, min(1, sets_delta + compliance.sets_delta))
        return _DayAdjustment(mult, sets_delta, discomfort_tokens)

    async def advance(self, user: User) -> WorkoutPlan:
        current = await self.plans.latest_for_user(user.id)
        if current is None:
            raise NotFound("No active plan to progress from")

        feedback = await self.feedback.latest_per_day_for_plan(current.id, user.id)
        if not feedback:
            raise BadRequest("Submit feedback for at least one day before progressing")

        by_day: dict[int, WorkoutFeedback] = {fb.day_id: fb for fb in feedback}

        discomfort: set[str] = set()
        for fb in feedback:
            discomfort.update(d for d in fb.discomfort if isinstance(d, str))
        discomfort_frozen = frozenset(discomfort)
        compliance_ratio = self._compliance_ratio(feedback)
        compliance = compliance_adjustment(compliance_ratio)

        next_week = current.week_number + 1
        scheduled_deload = self._is_deload_week(next_week)
        auto_deload = await self._auto_deload_decision(user.id, current.id, feedback, scheduled_deload)

        await self.plans.deactivate_all(user.id)

        new_plan = WorkoutPlan(
            user_id=user.id,
            name=self._next_name(current.name, current.week_number, next_week, auto_deload.should_deload),
            week_number=next_week,
            split_type=current.split_type,
            is_active=True,
            params={
                **(current.params or {}),
                "progressed_from": current.id,
                "deload": auto_deload.should_deload,
                "deload_reasons": list(auto_deload.reasons),
                "compliance_ratio": compliance_ratio,
                "compliance_adjustment": compliance.reason,
                "discomfort": sorted(discomfort_frozen),
            },
        )
        self.db.add(new_plan)
        await self.db.flush()

        for old_day in current.days:
            self._clone_day(
                new_plan.id,
                old_day,
                by_day.get(old_day.id),
                discomfort_frozen,
                auto_deload,
                compliance,
            )

        await self.db.commit()
        fresh = await self.plans.get_with_days(new_plan.id)
        assert fresh is not None
        return fresh

    def _clone_day(
        self,
        new_plan_id: int,
        old_day: WorkoutDay,
        fb: WorkoutFeedback | None,
        discomfort: frozenset[str],
        deload: AutoDeloadDecision,
        compliance: ComplianceAdjustment,
    ) -> None:
        new_day = WorkoutDay(
            plan_id=new_plan_id,
            day_index=old_day.day_index,
            title=old_day.title,
            focus=old_day.focus,
            is_rest=old_day.is_rest,
        )
        self.db.add(new_day)

        if old_day.is_rest:
            return

        adj = self._compute_adjustment(fb, discomfort, compliance)
        if deload.should_deload:
            adj = _DayAdjustment(
                intensity_mult=deload.intensity_mult,
                sets_delta=max(-2, min(1, deload.sets_delta + compliance.sets_delta)),
                skip_contras=adj.skip_contras,
            )

        for we in old_day.exercises:
            if adj.skip_contras & set(we.exercise.contraindications):
                continue
            new_weight = (
                round_to_plate(we.weight_kg * adj.intensity_mult)
                if we.weight_kg is not None
                else None
            )
            self.db.add(WorkoutExercise(
                day=new_day,
                exercise_id=we.exercise_id,
                position=we.position,
                sets=clamp_sets(we.sets + adj.sets_delta),
                reps_min=we.reps_min,
                reps_max=we.reps_max,
                weight_kg=new_weight,
                rest_sec=we.rest_sec,
                notes="Deload" if deload.should_deload else we.notes,
            ))

    @staticmethod
    def _next_name(current_name: str, current_week: int, next_week: int, deload: bool) -> str:
        suffix = " · Deload" if deload else ""
        marker = f"Week {current_week}"
        if marker in current_name:
            return current_name.replace(marker, f"Week {next_week}") + (suffix if not current_name.endswith(suffix) else "")
        return f"Week {next_week}{suffix}"

    async def _auto_deload_decision(
        self,
        user_id: int,
        plan_id: int,
        feedback_rows: list[WorkoutFeedback],
        scheduled_deload: bool,
    ) -> AutoDeloadDecision:
        missed_session_ratio = self._missed_session_ratio(feedback_rows)
        high_effort_ratio = self._high_effort_ratio(feedback_rows)
        e1rm_drop_ratio = await self._e1rm_drop_ratio(user_id, plan_id)
        return decide_auto_deload(
            scheduled_deload=scheduled_deload,
            e1rm_drop_ratio=e1rm_drop_ratio,
            high_effort_ratio=high_effort_ratio,
            missed_session_ratio=missed_session_ratio,
        )

    @staticmethod
    def _missed_session_ratio(rows: list[WorkoutFeedback]) -> float | None:
        if not rows:
            return None
        missed = sum(1 for row in rows if not row.completed)
        return missed / len(rows)

    @staticmethod
    def _high_effort_ratio(rows: list[WorkoutFeedback]) -> float | None:
        if not rows:
            return None
        high = sum(1 for row in rows if row.difficulty in {Difficulty.hard, Difficulty.very_hard})
        return high / len(rows)

    async def _e1rm_drop_ratio(self, user_id: int, plan_id: int) -> float | None:
        timeline = await self.set_logs.strength_timeline(user_id, limit=200)
        filtered = [row for row in timeline if isinstance(row, SetLog) and row.plan_id == plan_id]
        if len(filtered) < 8:
            return None
        midpoint = len(filtered) // 2
        early = filtered[:midpoint]
        recent = filtered[midpoint:]
        early_avg = sum(float(item.estimated_1rm) for item in early) / len(early)
        recent_avg = sum(float(item.estimated_1rm) for item in recent) / len(recent)
        if early_avg <= 0:
            return None
        drop_ratio = max(0.0, (early_avg - recent_avg) / early_avg)
        return round(drop_ratio, 4)

    @staticmethod
    def _compliance_ratio(rows: list[WorkoutFeedback]) -> float | None:
        if not rows:
            return None
        completed = sum(1 for row in rows if row.completed)
        return completed / len(rows)

    async def submit_feedback(
        self,
        user: User,
        day_id: int,
        completed: bool,
        difficulty: Difficulty,
        discomfort: list[str],
        note: str,
    ) -> WorkoutFeedback:
        day = await self.db.get(WorkoutDay, day_id)
        if day is None:
            raise NotFound("Day not found")
        plan = await self.plans.get(day.plan_id)
        if plan is None or plan.user_id != user.id:
            raise NotFound("Day not found")

        fb = await self.feedback.upsert(
            day_id=day_id, user_id=user.id,
            completed=completed, difficulty=difficulty,
            discomfort=discomfort, note=note,
        )
        await self.db.commit()
        await self.db.refresh(fb)
        return fb
