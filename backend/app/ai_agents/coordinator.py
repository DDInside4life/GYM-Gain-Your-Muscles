from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.config import ai_settings
from app.ai_agents.explanation_agent import ExplanationAgent, ExplanationOutput
from app.ai_agents.llm import LLMClient
from app.ai_agents.nutrition_agent import NutritionAgent, NutritionOutput
from app.ai_agents.progression_agent import ProgressionAgent, ProgressionOutput
from app.ai_agents.schemas import AIUserContext
from app.ai_agents.workout_agent import WorkoutAgentOutput, WorkoutGeneratorAgent
from app.models.nutrition import NutritionPlan
from app.models.user import User
from app.models.workout import WorkoutPlan
from app.repositories.ai_event import AIEventRepository
from app.schemas.nutrition import NutritionInput
from app.schemas.workout import WorkoutGenerateInput

logger = logging.getLogger("app.ai.coordinator")


@dataclass(slots=True)
class WorkoutWithExplanation:
    result: WorkoutAgentOutput
    explanation: ExplanationOutput


@dataclass(slots=True)
class ProgressionWithExplanation:
    result: ProgressionOutput
    explanation: ExplanationOutput


@dataclass(slots=True)
class NutritionWithExplanation:
    result: NutritionOutput
    explanation: ExplanationOutput


class AgentCoordinator:
    """Single entry-point the routes talk to.

    Orchestrates: safety → generator/progression/nutrition → explanation → log.
    Persists every call to `ai_events` for traceability and future learning.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._llm = LLMClient()
        self.workout = WorkoutGeneratorAgent(db, llm=self._llm)
        self.progression = ProgressionAgent(db, llm=self._llm)
        self.nutrition = NutritionAgent(db, llm=self._llm)
        self.explanation = ExplanationAgent(llm=self._llm)
        self.events = AIEventRepository(db)

    @staticmethod
    def is_ai_ready() -> bool:
        return ai_settings.is_ready

    async def generate_workout(
        self,
        user: User,
        payload: WorkoutGenerateInput,
    ) -> WorkoutWithExplanation:
        result = await self.workout.generate(user, payload)
        ctx = AIUserContext(
            user_id=user.id, age=payload.age,
            sex=user.sex.value if user.sex else None,
            weight_kg=payload.weight_kg, height_cm=payload.height_cm,
            experience=payload.experience, goal=payload.goal,
            equipment=payload.equipment, injuries=payload.injuries,
            days_per_week=payload.days_per_week,
        )
        plan_summary = self.workout.describe_plan(result.plan)
        explanation = await self.explanation.explain(
            ctx, plan_summary, kind="workout",
            extra={"rationale": result.rationale, "source": result.source},
        )
        self._persist_explanation(result.plan, explanation)
        await self.events.log(
            user_id=user.id, kind="workout", source=result.source,
            plan_id=result.plan.id, model=result.model,
            prompt=result.llm_prompt, response=result.llm_raw,
            output={"rationale": result.rationale, "warnings": result.warnings},
            explanation=explanation.block.model_dump(),
            latency_ms=result.latency_ms,
        )
        await self.db.commit()
        return WorkoutWithExplanation(result, explanation)

    async def advance_workout(self, user: User) -> ProgressionWithExplanation:
        result = await self.progression.advance(user)
        params = result.plan.params or {}
        ctx = AIUserContext(
            user_id=user.id, age=user.age,
            sex=user.sex.value if user.sex else None,
            weight_kg=user.weight_kg, height_cm=user.height_cm,
            experience=user.experience or params.get("experience", "intermediate"),
            goal=user.goal or params.get("goal", "general"),
            equipment=params.get("equipment", []),
            injuries=params.get("injuries", []),
            days_per_week=params.get("days_per_week", 4),
        )
        plan_summary = self.workout.describe_plan(result.plan)
        explanation = await self.explanation.explain(
            ctx, plan_summary, kind="progression",
            extra={"strategy": result.strategy, "rationale": result.rationale},
        )
        self._persist_explanation(result.plan, explanation)
        await self.events.log(
            user_id=user.id, kind="progression", source=result.source,
            plan_id=result.plan.id, model=result.model,
            prompt=result.llm_prompt, response=result.llm_raw,
            output={"strategy": result.strategy, "rationale": result.rationale,
                    "warnings": result.warnings},
            explanation=explanation.block.model_dump(),
            latency_ms=result.latency_ms,
        )
        await self.db.commit()
        return ProgressionWithExplanation(result, explanation)

    async def generate_nutrition(
        self,
        user: User,
        payload: NutritionInput,
    ) -> NutritionWithExplanation:
        result = await self.nutrition.generate(user, payload)
        ctx = AIUserContext(
            user_id=user.id, age=payload.age, sex=payload.sex.value,
            weight_kg=payload.weight_kg, height_cm=payload.height_cm,
            experience=user.experience or "intermediate",
            goal=payload.goal, equipment=[], injuries=[], days_per_week=4,
        )
        plan_summary = {
            "calories": result.plan.calories,
            "protein_g": result.plan.protein_g,
            "fat_g": result.plan.fat_g,
            "carbs_g": result.plan.carbs_g,
            "goal_label": result.plan.goal_label,
            "meals": [{"title": m.title, "calories": m.calories} for m in result.plan.meals],
        }
        explanation = await self.explanation.explain(
            ctx, plan_summary, kind="nutrition",
            extra={"rationale": result.rationale, "source": result.source},
        )
        await self.events.log(
            user_id=user.id, kind="nutrition", source=result.source,
            nutrition_plan_id=result.plan.id, model=result.model,
            prompt=result.llm_prompt, response=result.llm_raw,
            output={"rationale": result.rationale, "warnings": result.warnings},
            explanation=explanation.block.model_dump(),
            latency_ms=result.latency_ms,
        )
        await self.db.commit()
        return NutritionWithExplanation(result, explanation)

    @staticmethod
    def _persist_explanation(plan: WorkoutPlan, explanation: ExplanationOutput) -> None:
        params = dict(plan.params or {})
        params["explanation"] = explanation.block.model_dump()
        params["explanation_source"] = explanation.source
        plan.params = params
