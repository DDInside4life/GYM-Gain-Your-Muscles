from __future__ import annotations

import json
from typing import Any

from app.ai_agents.schemas import AIUserContext
from app.models.exercise import Exercise

WORKOUT_SYSTEM = (
    "You are GYM-AI, a senior strength & conditioning coach. "
    "You design safe, balanced, evidence-based weekly workout plans. "
    "Respond ONLY with a single JSON object matching the requested schema. "
    "Never invent exercise slugs — always pick from the provided catalogue. "
    "Never violate injury constraints. Never exceed per-day volume limits."
)

PROGRESSION_SYSTEM = (
    "You are GYM-AI progression coach. Given a user's last week plan and "
    "per-day feedback, decide next-week adjustments (overload / deload / maintain). "
    "Be conservative: drop intensity if any day was 'very_hard' or incomplete. "
    "Respond ONLY with valid JSON matching the schema."
)

NUTRITION_SYSTEM = (
    "You are GYM-AI nutritionist. Given calorie/macro targets and the user's "
    "profile, design a culturally-neutral meal split (3–5 meals). Use common "
    "whole foods, balance macros across meals. "
    "Respond ONLY with valid JSON matching the schema."
)

EXPLANATION_SYSTEM = (
    "You are GYM-AI. Produce a short, user-friendly explanation of WHY a plan "
    "was built this way. Plain language, specific, no marketing fluff. "
    "Respond ONLY with JSON matching the schema."
)


def _catalogue_summary(exercises: list[Exercise], limit_per_muscle: int = 8) -> list[dict[str, Any]]:
    """Compact catalogue view for prompts — top N per muscle to keep tokens low."""
    by_muscle: dict[str, list[Exercise]] = {}
    for ex in exercises:
        if not ex.is_active:
            continue
        by_muscle.setdefault(ex.primary_muscle.value, []).append(ex)

    out: list[dict[str, Any]] = []
    for muscle, pool in by_muscle.items():
        pool.sort(key=lambda e: (e.difficulty, e.id))
        for ex in pool[:limit_per_muscle]:
            out.append({
                "slug": ex.slug,
                "name": ex.name,
                "muscle": ex.primary_muscle.value,
                "equipment": ex.equipment.value,
                "category": ex.category.value,
                "difficulty": ex.difficulty,
                "contras": list(ex.contraindications),
            })
    return out


def build_workout_prompt(
    ctx: AIUserContext,
    catalogue: list[Exercise],
    safe_slugs: set[str],
    split_hint: str,
    scheme_hint: dict[str, int],
) -> str:
    catalogue_compact = [c for c in _catalogue_summary(catalogue) if c["slug"] in safe_slugs]
    schema = {
        "split_type": "string, e.g. full_body | upper_lower | ppl",
        "rationale": "1-3 sentences why this split/volume fits the user",
        "days": [
            {
                "day_index": "int 0..6 (Mon=0)",
                "title": "short day name",
                "focus": "comma-separated muscle groups",
                "is_rest": "bool",
                "exercises": [
                    {
                        "slug": "MUST come from allowed_slugs",
                        "sets": "int 2..6",
                        "reps_min": "int", "reps_max": "int",
                        "rest_sec": "int 30..300",
                        "rpe": "int 5..10",
                        "notes": "optional cue",
                    },
                ],
            },
        ],
    }
    payload = {
        "user": ctx.model_dump(),
        "constraints": {
            "days_per_week": ctx.days_per_week,
            "exercises_per_training_day": "4..6",
            "avoid_injury_tokens": ctx.injuries,
            "preferred_split": split_hint,
            "scheme_hint": scheme_hint,
        },
        "allowed_slugs": sorted(safe_slugs),
        "catalogue": catalogue_compact,
        "output_schema": schema,
        "rules": [
            "Return exactly days_per_week training days + rest days to fill a 7-day week.",
            "Use only slugs present in allowed_slugs. NEVER invent a new slug.",
            "Balance push/pull/legs across the week; no same muscle on 2 consecutive days.",
            "Respect scheme_hint for reps/rest; you may deviate ±20%.",
            "For beginners prefer difficulty<=3 and compound lifts first.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def build_progression_prompt(
    ctx: AIUserContext,
    last_week_summary: list[dict[str, Any]],
    is_deload_week: bool,
) -> str:
    schema = {
        "strategy": "overload | deload | maintain | volume_cut | mixed",
        "rationale": "1-3 sentences",
        "adjustments": [
            {
                "day_index": "int",
                "intensity_mult": "float 0.85..1.10",
                "sets_delta": "int -2..+2",
                "reason": "short cause",
            },
        ],
    }
    payload = {
        "user": ctx.model_dump(),
        "is_deload_week": is_deload_week,
        "last_week": last_week_summary,
        "output_schema": schema,
        "rules": [
            "If any day is very_hard OR not_completed → intensity_mult <= 1.0, sets_delta <= 0.",
            "If ALL days very_easy/easy → overload: intensity_mult 1.025..1.075, sets_delta 0..+1.",
            "If is_deload_week=true → strategy=deload, intensity_mult~0.9, sets_delta=-1 for every non-rest day.",
            "Never exceed ±7.5% intensity change.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def build_nutrition_prompt(
    ctx: AIUserContext,
    calories: int,
    protein_g: int,
    fat_g: int,
    carbs_g: int,
) -> str:
    schema = {
        "rationale": "1-3 sentences",
        "meals": [
            {
                "title": "e.g. Breakfast",
                "calories_ratio": "float 0.05..0.6 (ratios across meals will be normalized)",
                "items": [{"name": "food name", "amount_g": "float"}],
            },
        ],
    }
    payload = {
        "user": ctx.model_dump(),
        "targets": {
            "calories": calories, "protein_g": protein_g,
            "fat_g": fat_g, "carbs_g": carbs_g,
        },
        "output_schema": schema,
        "rules": [
            "3 to 5 meals. Ratios should roughly sum to 1.0 (we will re-normalize).",
            "High-protein meals must include a clear protein source (meat/fish/eggs/dairy/legumes).",
            "For fat_loss: prefer lean sources and fibrous vegetables.",
            "For muscle_gain: include starchy carbs post-workout (lunch or dinner).",
            "No supplements, no exotic ingredients.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def build_explanation_prompt(
    ctx: AIUserContext,
    plan_summary: dict[str, Any],
    extra_context: dict[str, Any] | None = None,
) -> str:
    schema = {
        "headline": "1 sentence, ≤140 chars",
        "bullets": ["3-5 short reasons (muscle balance, injury respect, volume fit, etc.)"],
        "warnings": ["safety/compliance warnings if any"],
        "next_steps": ["2-4 actionable tips for the upcoming week"],
    }
    payload = {
        "user": ctx.model_dump(),
        "plan": plan_summary,
        "context": extra_context or {},
        "output_schema": schema,
        "rules": [
            "Be concrete: cite sets, reps, rest or calorie target.",
            "No generic fitness fluff.",
            "If injuries are set → at least one bullet on how they were respected.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)
