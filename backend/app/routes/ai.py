from __future__ import annotations

from fastapi import APIRouter, status

from app.ai_agents import AgentCoordinator, ai_settings
from app.ai_agents.schemas import AIExplanationBlock
from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.repositories.ai_event import AIEventRepository
from app.repositories.workout import WorkoutPlanRepository
from app.schemas.ai import (
    AIExplanationRead, AINutritionPlanResponse, AIProgressionResponse,
    AIStatusResponse, AIWorkoutPlanResponse,
)
from app.schemas.nutrition import NutritionInput, NutritionPlanRead
from app.schemas.workout import WorkoutGenerateInput, WorkoutPlanRead

router = APIRouter()


def _explanation_read(block: AIExplanationBlock, source: str) -> AIExplanationRead:
    return AIExplanationRead(
        headline=block.headline,
        bullets=list(block.bullets),
        warnings=list(block.warnings),
        next_steps=list(block.next_steps),
        source=source,
    )


@router.get("/status", response_model=AIStatusResponse)
async def status_endpoint() -> AIStatusResponse:
    return AIStatusResponse(
        enabled=ai_settings.is_ready,
        provider=ai_settings.provider,
        model=ai_settings.model,
    )


@router.post(
    "/workouts/generate",
    response_model=AIWorkoutPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_ai_workout(
    payload: WorkoutGenerateInput, user: CurrentUser, db: DbSession,
) -> AIWorkoutPlanResponse:
    coord = AgentCoordinator(db)
    bundle = await coord.generate_workout(user, payload)
    return AIWorkoutPlanResponse(
        plan=WorkoutPlanRead.model_validate(bundle.result.plan),
        source=bundle.result.source,
        rationale=bundle.result.rationale,
        explanation=_explanation_read(bundle.explanation.block, bundle.explanation.source),
        warnings=bundle.result.warnings,
        latency_ms=bundle.result.latency_ms,
        model=bundle.result.model,
    )


@router.post(
    "/workouts/progress",
    response_model=AIProgressionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def progress_ai_workout(
    user: CurrentUser, db: DbSession,
) -> AIProgressionResponse:
    coord = AgentCoordinator(db)
    bundle = await coord.advance_workout(user)
    return AIProgressionResponse(
        plan=WorkoutPlanRead.model_validate(bundle.result.plan),
        source=bundle.result.source,
        strategy=bundle.result.strategy,
        rationale=bundle.result.rationale,
        explanation=_explanation_read(bundle.explanation.block, bundle.explanation.source),
        warnings=bundle.result.warnings,
        latency_ms=bundle.result.latency_ms,
        model=bundle.result.model,
    )


@router.post(
    "/nutrition/generate",
    response_model=AINutritionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_ai_nutrition(
    payload: NutritionInput, user: CurrentUser, db: DbSession,
) -> AINutritionPlanResponse:
    coord = AgentCoordinator(db)
    bundle = await coord.generate_nutrition(user, payload)
    return AINutritionPlanResponse(
        plan=NutritionPlanRead.model_validate(bundle.result.plan),
        source=bundle.result.source,
        rationale=bundle.result.rationale,
        explanation=_explanation_read(bundle.explanation.block, bundle.explanation.source),
        warnings=bundle.result.warnings,
        latency_ms=bundle.result.latency_ms,
        model=bundle.result.model,
    )


@router.get(
    "/plans/{plan_id}/explanation",
    response_model=AIExplanationRead,
)
async def plan_explanation(
    plan_id: int, user: CurrentUser, db: DbSession,
) -> AIExplanationRead:
    plan = await WorkoutPlanRepository(db).get(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("Plan not found")

    params = plan.params or {}
    explanation = params.get("explanation")
    source = params.get("explanation_source", "fallback")
    if explanation:
        return AIExplanationRead(
            headline=explanation.get("headline", ""),
            bullets=explanation.get("bullets", []),
            warnings=explanation.get("warnings", []),
            next_steps=explanation.get("next_steps", []),
            source=source,
        )

    event = await AIEventRepository(db).latest_for_plan(plan_id)
    if event and event.explanation:
        e = event.explanation
        return AIExplanationRead(
            headline=e.get("headline", ""),
            bullets=e.get("bullets", []),
            warnings=e.get("warnings", []),
            next_steps=e.get("next_steps", []),
            source=event.source,
        )

    raise NotFound("No explanation for this plan")
