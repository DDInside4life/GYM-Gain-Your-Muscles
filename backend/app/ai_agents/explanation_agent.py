from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from app.ai_agents.llm import LLMClient, LLMError, LLMResult
from app.ai_agents.prompts import EXPLANATION_SYSTEM, build_explanation_prompt
from app.ai_agents.schemas import AIExplanationBlock, AIUserContext

logger = logging.getLogger("app.ai.explanation")


@dataclass(slots=True)
class ExplanationOutput:
    block: AIExplanationBlock
    source: str  # "llm" | "fallback"
    llm_raw: str | None = None
    llm_prompt: str | None = None
    latency_ms: int = 0
    model: str | None = None


class ExplanationAgent:
    """Produces a structured 'why this plan' block for the UI."""

    def __init__(self, *, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    async def explain(
        self,
        ctx: AIUserContext,
        plan_summary: dict[str, Any],
        *,
        kind: str = "workout",
        extra: dict[str, Any] | None = None,
    ) -> ExplanationOutput:
        prompt = build_explanation_prompt(ctx, plan_summary, extra)
        llm_result: LLMResult | None = None
        try:
            llm_result = await self.llm.complete_json(
                system=EXPLANATION_SYSTEM, user=prompt, temperature=0.4, max_tokens=700,
            )
            block = AIExplanationBlock.model_validate(llm_result.data)
            return ExplanationOutput(
                block=block, source="llm",
                llm_raw=llm_result.raw, llm_prompt=prompt,
                latency_ms=llm_result.latency_ms, model=llm_result.model,
            )
        except (LLMError, ValidationError) as exc:
            logger.info("AI explanation fallback (%s): %s", type(exc).__name__, exc)
            return ExplanationOutput(
                block=self._fallback(ctx, plan_summary, kind),
                source="fallback",
                llm_raw=llm_result.raw if llm_result else None,
                llm_prompt=prompt,
                latency_ms=llm_result.latency_ms if llm_result else 0,
                model=llm_result.model if llm_result else None,
            )

    @staticmethod
    def _fallback(
        ctx: AIUserContext,
        plan_summary: dict[str, Any],
        kind: str,
    ) -> AIExplanationBlock:
        if kind == "nutrition":
            cal = plan_summary.get("calories") or "target"
            return AIExplanationBlock(
                headline=f"Plan targets {cal} kcal matched to your {ctx.goal.value} goal.",
                bullets=[
                    f"Protein set at ~{plan_summary.get('protein_g','?')} g to preserve/build lean mass.",
                    f"Fat at ~{plan_summary.get('fat_g','?')} g for hormonal health.",
                    "Carbs fill the remainder, enough to fuel training volume.",
                ],
                warnings=[],
                next_steps=[
                    "Weigh yourself 3× / week at the same time of day.",
                    "Adjust calories by ±10% after 2 weeks if trend is flat.",
                ],
            )
        days = plan_summary.get("days", [])
        non_rest = [d for d in days if not d.get("is_rest")]
        bullets = [
            f"{ctx.days_per_week} training days · split: {plan_summary.get('split_type','?')}",
            f"Each training day has {len(non_rest[0]['exercises']) if non_rest else '4–6'} exercises targeting distinct muscle groups.",
            f"Intensity tuned for {ctx.experience.value} {ctx.goal.value}.",
        ]
        if ctx.injuries:
            bullets.append(f"Exercises loading {', '.join(ctx.injuries)} were excluded.")
        return AIExplanationBlock(
            headline=f"{ctx.goal.value.replace('_',' ').title()} plan, week {plan_summary.get('week_number', '?')}",
            bullets=bullets,
            warnings=[],
            next_steps=[
                "Log difficulty after each workout — the coach uses it to adjust next week.",
                "Keep rest between sets within the prescribed window.",
            ],
        )
