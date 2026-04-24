from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.llm import LLMClient, LLMError, LLMResult
from app.ai_agents.prompts import NUTRITION_SYSTEM, build_nutrition_prompt
from app.ai_agents.schemas import AINutritionDraft, AIUserContext
from app.models.nutrition import NutritionPlan, PlanMeal
from app.models.user import User
from app.schemas.nutrition import NutritionInput
from app.services.nutrition import NutritionService, MEAL_TEMPLATES

logger = logging.getLogger("app.ai.nutrition")


@dataclass(slots=True)
class NutritionOutput:
    plan: NutritionPlan
    source: str  # "llm" | "fallback"
    rationale: str
    llm_raw: str | None = None
    llm_prompt: str | None = None
    latency_ms: int = 0
    model: str | None = None
    warnings: list[str] = field(default_factory=list)


class NutritionAgent:
    """Deterministic calorie/macro math + LLM-assisted meal structure.

    Calories, protein/fat/carbs are ALWAYS computed by the existing service
    (Mifflin-St Jeor etc). LLM only personalizes the meal split.
    """

    def __init__(self, db: AsyncSession, *, llm: LLMClient | None = None) -> None:
        self.db = db
        self.llm = llm or LLMClient()
        self.base = NutritionService(db)

    async def generate(self, user: User, payload: NutritionInput) -> NutritionOutput:
        bmr = self.base.mifflin_st_jeor(payload.weight_kg, payload.height_cm, payload.age, payload.sex)
        tdee = int(round(bmr * payload.activity_factor))
        calories, label = self.base.adjust_for_goal(tdee, payload.goal)
        protein_g, fat_g, carbs_g = self.base.macro_split(calories, payload.goal, payload.weight_kg)

        plan = NutritionPlan(
            user_id=user.id, calories=calories, protein_g=protein_g, fat_g=fat_g, carbs_g=carbs_g,
            bmr=bmr, tdee=tdee, goal_label=label,
        )
        self.db.add(plan)
        await self.db.flush()

        ctx = AIUserContext(
            user_id=user.id, age=payload.age, sex=payload.sex.value,
            weight_kg=payload.weight_kg, height_cm=payload.height_cm,
            experience=user.experience or "intermediate",
            goal=payload.goal, equipment=[], injuries=[],
            days_per_week=4,
        )

        prompt = build_nutrition_prompt(ctx, calories, protein_g, fat_g, carbs_g)
        llm_result: LLMResult | None = None
        source = "llm"
        rationale = ""
        warnings: list[str] = []

        meals_to_write: list[tuple[str, float, list[dict]]] = []
        try:
            llm_result = await self.llm.complete_json(system=NUTRITION_SYSTEM, user=prompt)
            draft = AINutritionDraft.model_validate(llm_result.data)
            rationale = draft.rationale
            for m in draft.meals:
                meals_to_write.append((
                    m.title,
                    m.calories_ratio,
                    [{"name": it.name, "amount_g": it.amount_g} for it in m.items],
                ))
        except (LLMError, ValidationError) as exc:
            logger.info("AI nutrition fallback (%s): %s", type(exc).__name__, exc)
            source = "fallback"
            rationale = f"Deterministic meal template ({label})"
            warnings.append(f"llm_failed: {type(exc).__name__}")
            meals_to_write = [(t, r, items) for t, r, items in MEAL_TEMPLATES]

        for idx, (title, ratio, items) in enumerate(meals_to_write):
            self.db.add(PlanMeal(
                plan_id=plan.id, position=idx, title=title,
                calories=int(calories * ratio),
                protein_g=round(protein_g * ratio, 1),
                fat_g=round(fat_g * ratio, 1),
                carbs_g=round(carbs_g * ratio, 1),
                items=items,
            ))
        await self.db.commit()
        await self.db.refresh(plan, ["meals"])

        return NutritionOutput(
            plan=plan, source=source, rationale=rationale,
            llm_raw=llm_result.raw if llm_result else None,
            llm_prompt=prompt,
            latency_ms=llm_result.latency_ms if llm_result else 0,
            model=llm_result.model if llm_result else None,
            warnings=warnings,
        )
