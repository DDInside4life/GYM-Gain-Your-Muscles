from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.llm import LLMClient, LLMError, LLMResult
from app.ai_agents.prompts import PROGRESSION_SYSTEM, build_progression_prompt
from app.ai_agents.schemas import AIProgressionDraft, AIUserContext
from app.core.exceptions import BadRequest, NotFound
from app.models.user import User
from app.models.workout import WorkoutDay, WorkoutExercise, WorkoutFeedback, WorkoutPlan
from app.repositories.workout import WorkoutFeedbackRepository, WorkoutPlanRepository
from app.services.workout.progression import ProgressionService
from app.services.workout.rules import (
    DELOAD_EVERY_WEEKS, clamp_sets, resolve_injury_contras, round_to_plate,
)

logger = logging.getLogger("app.ai.progression")


@dataclass(slots=True)
class ProgressionOutput:
    plan: WorkoutPlan
    source: str  # "llm" | "fallback"
    strategy: str
    rationale: str
    llm_raw: str | None = None
    llm_prompt: str | None = None
    latency_ms: int = 0
    model: str | None = None
    warnings: list[str] = field(default_factory=list)


class ProgressionAgent:
    """Adjusts next week based on feedback. LLM proposes, rules enforce bounds."""

    def __init__(self, db: AsyncSession, *, llm: LLMClient | None = None) -> None:
        self.db = db
        self.llm = llm or LLMClient()
        self.plans = WorkoutPlanRepository(db)
        self.feedback = WorkoutFeedbackRepository(db)
        self.fallback = ProgressionService(db)

    async def advance(self, user: User) -> ProgressionOutput:
        current = await self.plans.latest_for_user(user.id)
        if current is None:
            raise NotFound("No active plan to progress from")

        feedback = await self.feedback.latest_per_day_for_plan(current.id, user.id)
        if not feedback:
            raise BadRequest("Submit feedback for at least one day before progressing")

        ctx = self._build_context(user, current)
        last_week_summary = self._summarize_week(current, feedback)
        is_deload = (current.week_number + 1) % DELOAD_EVERY_WEEKS == 0

        prompt = build_progression_prompt(ctx, last_week_summary, is_deload)
        llm_result: LLMResult | None = None
        try:
            llm_result = await self.llm.complete_json(system=PROGRESSION_SYSTEM, user=prompt)
            draft = AIProgressionDraft.model_validate(llm_result.data)
            plan = await self._apply(user, current, feedback, draft, is_deload)
            await self.db.commit()
            fresh = await self.plans.get_with_days(plan.id)
            assert fresh is not None
            return ProgressionOutput(
                plan=fresh,
                source="llm",
                strategy=draft.strategy,
                rationale=draft.rationale,
                llm_raw=llm_result.raw,
                llm_prompt=prompt,
                latency_ms=llm_result.latency_ms,
                model=llm_result.model,
            )
        except (LLMError, ValidationError) as exc:
            logger.info("AI progression fallback (%s): %s", type(exc).__name__, exc)
            plan = await self.fallback.advance(user)
            return ProgressionOutput(
                plan=plan,
                source="fallback",
                strategy="deload" if is_deload else "rule_based",
                rationale="Deterministic progression rules applied.",
                llm_raw=llm_result.raw if llm_result else None,
                llm_prompt=prompt,
                latency_ms=llm_result.latency_ms if llm_result else 0,
                model=llm_result.model if llm_result else None,
                warnings=[f"llm_failed: {type(exc).__name__}"],
            )

    @staticmethod
    def _build_context(user: User, current: WorkoutPlan) -> AIUserContext:
        params = current.params or {}
        return AIUserContext(
            user_id=user.id,
            age=user.age,
            sex=user.sex.value if user.sex else None,
            weight_kg=user.weight_kg,
            height_cm=user.height_cm,
            experience=user.experience or params.get("experience", "intermediate"),
            goal=user.goal or params.get("goal", "general"),
            equipment=params.get("equipment", []),
            injuries=params.get("injuries", []),
            days_per_week=params.get("days_per_week", 4),
        )

    @staticmethod
    def _summarize_week(
        plan: WorkoutPlan,
        feedback: list[WorkoutFeedback],
    ) -> list[dict[str, Any]]:
        by_day = {fb.day_id: fb for fb in feedback}
        out: list[dict[str, Any]] = []
        for d in plan.days:
            fb = by_day.get(d.id)
            out.append({
                "day_index": d.day_index,
                "title": d.title,
                "is_rest": d.is_rest,
                "num_exercises": len(d.exercises),
                "total_sets": sum(we.sets for we in d.exercises),
                "feedback": {
                    "completed": fb.completed if fb else None,
                    "difficulty": fb.difficulty.value if fb else None,
                    "discomfort": list(fb.discomfort) if fb else [],
                    "note": fb.note if fb else "",
                } if not d.is_rest else None,
            })
        return out

    async def _apply(
        self,
        user: User,
        current: WorkoutPlan,
        feedback: list[WorkoutFeedback],
        draft: AIProgressionDraft,
        is_deload: bool,
    ) -> WorkoutPlan:
        by_day = {fb.day_id: fb for fb in feedback}
        adj_by_idx = {a.day_index: a for a in draft.adjustments}

        discomfort: set[str] = set()
        for fb in feedback:
            discomfort.update(d for d in fb.discomfort if isinstance(d, str))
        contras = resolve_injury_contras(list(discomfort)) | resolve_injury_contras(
            (current.params or {}).get("injuries") or []
        )

        next_week = current.week_number + 1
        await self.plans.deactivate_all(user.id)
        new_plan = WorkoutPlan(
            user_id=user.id,
            name=self._next_name(current.name, current.week_number, next_week, is_deload, draft.strategy),
            week_number=next_week,
            split_type=current.split_type,
            is_active=True,
            params={
                **(current.params or {}),
                "ai": True,
                "source": "llm",
                "progressed_from": current.id,
                "deload": is_deload,
                "strategy": draft.strategy,
                "rationale": draft.rationale,
                "discomfort": sorted(discomfort),
            },
        )
        self.db.add(new_plan)
        await self.db.flush()

        for old_day in current.days:
            self._clone_day(new_plan.id, old_day, by_day.get(old_day.id),
                            adj_by_idx.get(old_day.day_index), contras, is_deload)

        return new_plan

    def _clone_day(
        self,
        new_plan_id: int,
        old_day: WorkoutDay,
        fb: WorkoutFeedback | None,
        adjustment: Any | None,
        contras: frozenset[str],
        is_deload: bool,
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

        if adjustment is not None:
            intensity_mult = float(adjustment.intensity_mult)
            sets_delta = int(adjustment.sets_delta)
        elif is_deload:
            intensity_mult, sets_delta = 0.9, -1
        else:
            intensity_mult, sets_delta = 1.0, 0

        if fb is not None and (not fb.completed or fb.difficulty.value == "very_hard"):
            intensity_mult = min(intensity_mult, 0.95)
            sets_delta = min(sets_delta, 0)
        intensity_mult = max(0.85, min(1.10, intensity_mult))

        for we in old_day.exercises:
            if contras & set(we.exercise.contraindications):
                continue
            new_weight = (
                round_to_plate(we.weight_kg * intensity_mult)
                if we.weight_kg is not None else None
            )
            self.db.add(WorkoutExercise(
                day=new_day,
                exercise_id=we.exercise_id,
                position=we.position,
                sets=clamp_sets(we.sets + sets_delta),
                reps_min=we.reps_min,
                reps_max=we.reps_max,
                weight_kg=new_weight,
                rest_sec=we.rest_sec,
                notes="Deload" if is_deload else we.notes,
            ))

    @staticmethod
    def _next_name(
        current_name: str, current_week: int, next_week: int,
        deload: bool, strategy: str,
    ) -> str:
        suffix = " · Deload" if deload else f" · AI {strategy}"
        marker = f"Week {current_week}"
        if marker in current_name:
            return current_name.replace(marker, f"Week {next_week}") + suffix
        return f"Week {next_week}{suffix}"
