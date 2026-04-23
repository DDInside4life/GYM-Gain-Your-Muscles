from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.llm import LLMClient, LLMError, LLMResult
from app.ai_agents.prompts import WORKOUT_SYSTEM, build_workout_prompt
from app.ai_agents.safety_agent import SafetyAgent, SafetyFilterResult
from app.ai_agents.schemas import AIUserContext, AIWorkoutDraft
from app.models.exercise import Exercise
from app.models.user import User
from app.models.workout import WorkoutDay, WorkoutExercise, WorkoutPlan
from app.repositories.exercise import ExerciseRepository
from app.repositories.workout import WorkoutPlanRepository
from app.schemas.workout import WorkoutGenerateInput
from app.services.workout.generator import WorkoutGenerator
from app.services.workout.rules import GOAL_SCHEME, clamp_sets, round_to_plate
from app.services.workout.splits import pick_split

logger = logging.getLogger("app.ai.workout")


@dataclass(slots=True)
class WorkoutAgentOutput:
    plan: WorkoutPlan
    source: str  # "llm" | "fallback"
    rationale: str
    llm_raw: str | None = None
    llm_prompt: str | None = None
    latency_ms: int = 0
    model: str | None = None
    warnings: list[str] = field(default_factory=list)


class WorkoutGeneratorAgent:
    """LLM-first plan generator with deterministic fallback + safety sandwich.

    Contract: always returns a persisted WorkoutPlan. Never raises for
    LLM failures — downgrades silently to the existing WorkoutGenerator.
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        llm: LLMClient | None = None,
        safety: SafetyAgent | None = None,
    ) -> None:
        self.db = db
        self.llm = llm or LLMClient()
        self.safety = safety or SafetyAgent()
        self.exercises = ExerciseRepository(db)
        self.plans = WorkoutPlanRepository(db)
        self.fallback = WorkoutGenerator(db)

    async def generate(
        self,
        user: User,
        payload: WorkoutGenerateInput,
    ) -> WorkoutAgentOutput:
        ctx = self._build_context(user, payload)
        catalogue = await self.exercises.list_filtered(active_only=True)
        if not catalogue:
            raise ValueError("Exercise catalogue is empty")

        safety = self.safety.filter_catalogue(ctx, catalogue)
        split_hint = pick_split(ctx.days_per_week, ctx.experience)
        scheme = GOAL_SCHEME[ctx.goal]
        scheme_hint = {
            "sets": scheme.sets, "reps_min": scheme.reps_min, "reps_max": scheme.reps_max,
            "rest_sec": scheme.rest_sec, "rpe": scheme.rpe,
        }

        prompt = build_workout_prompt(ctx, catalogue, set(safety.safe_slugs), split_hint, scheme_hint)

        llm_result: LLMResult | None = None
        warnings: list[str] = []
        try:
            llm_result = await self.llm.complete_json(system=WORKOUT_SYSTEM, user=prompt)
            draft = AIWorkoutDraft.model_validate(llm_result.data)
            plan = await self._materialize(user, ctx, draft, catalogue, safety, warnings)
            await self.db.commit()
            fresh = await self.plans.get_with_days(plan.id)
            assert fresh is not None
            return WorkoutAgentOutput(
                plan=fresh,
                source="llm",
                rationale=draft.rationale or f"{split_hint} split, {ctx.days_per_week} days/week",
                llm_raw=llm_result.raw,
                llm_prompt=prompt,
                latency_ms=llm_result.latency_ms,
                model=llm_result.model,
                warnings=warnings,
            )
        except (LLMError, ValidationError, ValueError) as exc:
            logger.info("AI workout fallback (%s): %s", type(exc).__name__, exc)
            plan = await self.fallback.generate(user, payload)
            return WorkoutAgentOutput(
                plan=plan,
                source="fallback",
                rationale=f"Deterministic generator ({split_hint} split)",
                llm_raw=llm_result.raw if llm_result else None,
                llm_prompt=prompt,
                latency_ms=llm_result.latency_ms if llm_result else 0,
                model=llm_result.model if llm_result else None,
                warnings=warnings + [f"llm_failed: {type(exc).__name__}"],
            )

    @staticmethod
    def _build_context(user: User, payload: WorkoutGenerateInput) -> AIUserContext:
        return AIUserContext(
            user_id=user.id,
            age=payload.age,
            sex=user.sex.value if user.sex else None,
            weight_kg=payload.weight_kg,
            height_cm=payload.height_cm,
            experience=payload.experience,
            goal=payload.goal,
            equipment=payload.equipment,
            injuries=payload.injuries,
            days_per_week=payload.days_per_week,
        )

    async def _materialize(
        self,
        user: User,
        ctx: AIUserContext,
        draft: AIWorkoutDraft,
        catalogue: list[Exercise],
        safety: SafetyFilterResult,
        warnings: list[str],
    ) -> WorkoutPlan:
        by_slug: dict[str, Exercise] = {ex.slug: ex for ex in catalogue}

        prev = await self.plans.latest_for_user(user.id)
        next_week = (prev.week_number + 1) if prev else 1
        await self.plans.deactivate_all(user.id)

        scheme = GOAL_SCHEME[ctx.goal]
        plan = WorkoutPlan(
            user_id=user.id,
            name=f"Week {next_week} · AI · {draft.split_type.replace('_', ' ').title()}",
            week_number=next_week,
            split_type=draft.split_type,
            is_active=True,
            params={
                "ai": True,
                "source": "llm",
                "goal": ctx.goal.value,
                "experience": ctx.experience.value,
                "days_per_week": ctx.days_per_week,
                "equipment": sorted(e.value for e in safety.equipment),
                "injuries": ctx.injuries,
                "rationale": draft.rationale,
                "scheme": {
                    "sets": scheme.sets, "reps_min": scheme.reps_min,
                    "reps_max": scheme.reps_max, "rest_sec": scheme.rest_sec, "rpe": scheme.rpe,
                },
            },
        )
        self.db.add(plan)
        await self.db.flush()

        seen_days: set[int] = set()
        for raw_day in draft.days:
            if raw_day.day_index in seen_days:
                warnings.append(f"duplicate_day_{raw_day.day_index}_dropped")
                continue
            seen_days.add(raw_day.day_index)

            day = WorkoutDay(
                plan_id=plan.id,
                day_index=raw_day.day_index,
                title=raw_day.title[:60],
                focus=raw_day.focus[:60],
                is_rest=raw_day.is_rest,
            )
            self.db.add(day)
            await self.db.flush()

            if raw_day.is_rest:
                continue

            added = 0
            for pos, ref in enumerate(raw_day.exercises):
                ex = by_slug.get(ref.slug)
                if ex is None or not self.safety.is_exercise_safe(ex, safety):
                    warnings.append(f"unsafe_or_unknown_slug:{ref.slug}")
                    continue
                weight = self._estimate_weight(user, ex, ctx)
                self.db.add(WorkoutExercise(
                    day_id=day.id,
                    exercise_id=ex.id,
                    position=pos,
                    sets=clamp_sets(ref.sets),
                    reps_min=ref.reps_min,
                    reps_max=max(ref.reps_max, ref.reps_min),
                    weight_kg=weight,
                    rest_sec=ref.rest_sec,
                    notes=(ref.notes or f"RPE ~{ref.rpe}")[:240],
                ))
                added += 1

            if added == 0:
                warnings.append(f"empty_day_{raw_day.day_index}_filled_by_fallback")
                await self._fill_empty_day(day, ctx, catalogue, safety)

        self._fill_missing_rest_days(plan.id, seen_days)
        return plan

    def _fill_missing_rest_days(self, plan_id: int, seen: set[int]) -> None:
        for i in range(7):
            if i in seen:
                continue
            self.db.add(WorkoutDay(
                plan_id=plan_id, day_index=i, title="Rest", focus="recovery", is_rest=True,
            ))

    async def _fill_empty_day(
        self,
        day: WorkoutDay,
        ctx: AIUserContext,
        catalogue: list[Exercise],
        safety: SafetyFilterResult,
    ) -> None:
        scheme = GOAL_SCHEME[ctx.goal]
        filler = sorted(
            (ex for ex in catalogue if ex.slug in safety.safe_slugs),
            key=lambda e: (e.difficulty, e.id),
        )[:4]
        for pos, ex in enumerate(filler):
            self.db.add(WorkoutExercise(
                day_id=day.id, exercise_id=ex.id, position=pos,
                sets=scheme.sets, reps_min=scheme.reps_min, reps_max=scheme.reps_max,
                weight_kg=None, rest_sec=scheme.rest_sec, notes="Safe filler",
            ))

    @staticmethod
    def _estimate_weight(user: User, ex: Exercise, ctx: AIUserContext) -> float | None:
        from app.models.exercise import Equipment as Eq, ExerciseCategory
        from app.services.workout.generator import MUSCLE_LOAD_FACTOR
        from app.services.workout.rules import EXPERIENCE_INTENSITY_MOD, GOAL_INTENSITY_MOD

        if ex.equipment == Eq.bodyweight or ex.category == ExerciseCategory.cardio:
            return None
        bw = ctx.weight_kg or user.weight_kg or 75.0
        raw = (
            bw
            * EXPERIENCE_INTENSITY_MOD[ctx.experience]
            * GOAL_INTENSITY_MOD[ctx.goal]
            * MUSCLE_LOAD_FACTOR.get(ex.primary_muscle, 0.6)
        )
        return round_to_plate(raw)

    def describe_plan(self, plan: WorkoutPlan) -> dict[str, Any]:
        """Compact plan snapshot for use in prompts / events log."""
        return {
            "name": plan.name,
            "split_type": plan.split_type,
            "week_number": plan.week_number,
            "days": [
                {
                    "day_index": d.day_index,
                    "title": d.title,
                    "focus": d.focus,
                    "is_rest": d.is_rest,
                    "exercises": [
                        {
                            "slug": we.exercise.slug,
                            "sets": we.sets,
                            "reps": f"{we.reps_min}-{we.reps_max}",
                            "weight_kg": we.weight_kg,
                            "rest_sec": we.rest_sec,
                        }
                        for we in d.exercises
                    ],
                }
                for d in plan.days
            ],
        }
