from __future__ import annotations

from pydantic import BaseModel

from app.schemas.nutrition import NutritionPlanRead
from app.schemas.workout import WorkoutPlanRead


class AIExplanationRead(BaseModel):
    headline: str
    bullets: list[str]
    warnings: list[str]
    next_steps: list[str]
    source: str  # "llm" | "fallback"


class AIWorkoutPlanResponse(BaseModel):
    plan: WorkoutPlanRead
    source: str  # "llm" | "fallback"
    rationale: str
    explanation: AIExplanationRead
    warnings: list[str] = []
    latency_ms: int = 0
    model: str | None = None


class AINutritionPlanResponse(BaseModel):
    plan: NutritionPlanRead
    source: str
    rationale: str
    explanation: AIExplanationRead
    warnings: list[str] = []
    latency_ms: int = 0
    model: str | None = None


class AIProgressionResponse(BaseModel):
    plan: WorkoutPlanRead
    source: str
    strategy: str
    rationale: str
    explanation: AIExplanationRead
    warnings: list[str] = []
    latency_ms: int = 0
    model: str | None = None


class AIStatusResponse(BaseModel):
    enabled: bool
    provider: str
    model: str
