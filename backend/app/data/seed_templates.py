from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exercise import Exercise
from app.models.workout_template import TemplateDay, TemplateExercise, WorkoutTemplate


@dataclass(slots=True)
class TemplateExerciseSeed:
    slug: str
    sets: int
    reps_min: int
    reps_max: int
    rest_sec: int
    target_percent_1rm: float | None = None
    notes: str = ""


@dataclass(slots=True)
class TemplateDaySeed:
    day_index: int
    title: str
    focus: str
    exercises: list[TemplateExerciseSeed]


@dataclass(slots=True)
class TemplateSeed:
    slug: str
    name: str
    level: str
    split_type: str
    days_per_week: int
    description: str
    days: list[TemplateDaySeed]


TEMPLATES: list[TemplateSeed] = [
    TemplateSeed(
        slug="full-body-foundation",
        name="Full Body Foundation",
        level="beginner",
        split_type="full_body",
        days_per_week=3,
        description="Базовая полнотельная программа для старта с акцентом на технику и прогрессию.",
        days=[
            TemplateDaySeed(0, "Day 1 · Full Body", "chest, back, legs", [
                TemplateExerciseSeed("barbell-back-squat", 4, 6, 8, 150, 0.72),
                TemplateExerciseSeed("bench-press", 4, 6, 8, 150, 0.72),
                TemplateExerciseSeed("barbell-row", 3, 8, 10, 120, 0.68),
                TemplateExerciseSeed("plank", 3, 30, 45, 60, None, "seconds"),
            ]),
            TemplateDaySeed(1, "Day 2 · Full Body", "legs, shoulders, back", [
                TemplateExerciseSeed("leg-press", 4, 10, 12, 120, 0.67),
                TemplateExerciseSeed("seated-db-press", 4, 8, 10, 120, 0.68),
                TemplateExerciseSeed("lat-pulldown", 4, 8, 12, 120, 0.68),
                TemplateExerciseSeed("hanging-leg-raise", 3, 10, 15, 75),
            ]),
            TemplateDaySeed(2, "Day 3 · Full Body", "posterior chain, chest, arms", [
                TemplateExerciseSeed("romanian-deadlift", 4, 6, 8, 150, 0.7),
                TemplateExerciseSeed("incline-bench", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("pull-up", 4, 6, 10, 120),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 15, 75),
                TemplateExerciseSeed("biceps-curl", 3, 10, 15, 75),
            ]),
        ],
    ),
    TemplateSeed(
        slug="upper-lower-performance",
        name="Upper / Lower Performance",
        level="intermediate",
        split_type="upper_lower",
        days_per_week=4,
        description="Классический 4-дневный Upper/Lower для силы и гипертрофии.",
        days=[
            TemplateDaySeed(0, "Day 1 · Upper A", "chest, back, shoulders", [
                TemplateExerciseSeed("bench-press", 5, 5, 6, 180, 0.78),
                TemplateExerciseSeed("barbell-row", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("seated-db-press", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 12, 75),
                TemplateExerciseSeed("hammer-curl", 3, 10, 12, 75),
            ]),
            TemplateDaySeed(1, "Day 2 · Lower A", "legs, glutes", [
                TemplateExerciseSeed("barbell-back-squat", 5, 5, 6, 180, 0.8),
                TemplateExerciseSeed("romanian-deadlift", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("leg-extension", 3, 12, 15, 75),
                TemplateExerciseSeed("leg-curl", 3, 12, 15, 75),
                TemplateExerciseSeed("calf-raise", 4, 10, 15, 60),
            ]),
            TemplateDaySeed(2, "Day 3 · Upper B", "chest, back, arms", [
                TemplateExerciseSeed("incline-bench", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("lat-pulldown", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("close-grip-bench", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("face-pull", 3, 12, 15, 75),
                TemplateExerciseSeed("preacher-curl", 3, 10, 12, 75),
            ]),
            TemplateDaySeed(3, "Day 4 · Lower B", "legs, glutes, core", [
                TemplateExerciseSeed("leg-press", 4, 8, 12, 120, 0.7),
                TemplateExerciseSeed("hip-thrust", 4, 8, 10, 120, 0.72),
                TemplateExerciseSeed("bulgarian-split-squat", 3, 8, 10, 90),
                TemplateExerciseSeed("walking-lunges", 3, 10, 14, 90),
                TemplateExerciseSeed("cable-crunch", 3, 12, 15, 60),
            ]),
        ],
    ),
    TemplateSeed(
        slug="push-pull-legs-progression",
        name="Push Pull Legs Progression",
        level="intermediate",
        split_type="push_pull_legs",
        days_per_week=6,
        description="PPL сплит с удвоением частоты для набора массы и силы.",
        days=[
            TemplateDaySeed(0, "Day 1 · Push", "chest, shoulders, triceps", [
                TemplateExerciseSeed("bench-press", 4, 5, 8, 150, 0.76),
                TemplateExerciseSeed("incline-bench", 4, 8, 10, 120, 0.72),
                TemplateExerciseSeed("seated-db-press", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 15, 75),
            ]),
            TemplateDaySeed(1, "Day 2 · Pull", "back, biceps", [
                TemplateExerciseSeed("deadlift", 3, 3, 5, 180, 0.82),
                TemplateExerciseSeed("pull-up", 4, 6, 10, 120),
                TemplateExerciseSeed("barbell-row", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("hammer-curl", 3, 10, 12, 75),
            ]),
            TemplateDaySeed(2, "Day 3 · Legs", "legs, glutes, calves", [
                TemplateExerciseSeed("barbell-back-squat", 5, 5, 8, 180, 0.78),
                TemplateExerciseSeed("leg-press", 4, 10, 12, 120, 0.7),
                TemplateExerciseSeed("romanian-deadlift", 4, 8, 10, 150, 0.72),
                TemplateExerciseSeed("calf-raise", 4, 12, 15, 75),
            ]),
            TemplateDaySeed(3, "Day 4 · Push B", "chest, shoulders, triceps", [
                TemplateExerciseSeed("close-grip-bench", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("db-fly", 3, 12, 15, 75),
                TemplateExerciseSeed("lateral-raise", 4, 12, 20, 60),
                TemplateExerciseSeed("dips", 3, 8, 12, 90),
            ]),
            TemplateDaySeed(4, "Day 5 · Pull B", "back, rear delts, biceps", [
                TemplateExerciseSeed("lat-pulldown", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("barbell-row", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("face-pull", 4, 12, 15, 60),
                TemplateExerciseSeed("preacher-curl", 3, 10, 12, 75),
            ]),
            TemplateDaySeed(5, "Day 6 · Legs B", "legs, glutes", [
                TemplateExerciseSeed("hip-thrust", 4, 8, 12, 120, 0.72),
                TemplateExerciseSeed("bulgarian-split-squat", 3, 10, 12, 90),
                TemplateExerciseSeed("leg-extension", 3, 12, 15, 60),
                TemplateExerciseSeed("leg-curl", 3, 12, 15, 60),
            ]),
        ],
    ),
    TemplateSeed(
        slug="bro-split-classic",
        name="Bro Split Classic",
        level="intermediate",
        split_type="bro_split",
        days_per_week=5,
        description="Традиционный бодибилдинг-сплит с одним фокусом на мышечную группу в день.",
        days=[
            TemplateDaySeed(0, "Day 1 · Chest", "chest", [
                TemplateExerciseSeed("bench-press", 5, 5, 8, 150, 0.76),
                TemplateExerciseSeed("incline-bench", 4, 8, 10, 120, 0.72),
                TemplateExerciseSeed("db-fly", 4, 10, 15, 75),
                TemplateExerciseSeed("push-up", 3, 12, 20, 60),
            ]),
            TemplateDaySeed(1, "Day 2 · Back", "back", [
                TemplateExerciseSeed("deadlift", 4, 3, 5, 180, 0.84),
                TemplateExerciseSeed("pull-up", 4, 6, 10, 120),
                TemplateExerciseSeed("barbell-row", 4, 6, 8, 150, 0.74),
                TemplateExerciseSeed("lat-pulldown", 3, 10, 12, 90, 0.68),
            ]),
            TemplateDaySeed(2, "Day 3 · Legs", "legs", [
                TemplateExerciseSeed("barbell-back-squat", 5, 5, 8, 180, 0.78),
                TemplateExerciseSeed("leg-press", 4, 10, 12, 120, 0.7),
                TemplateExerciseSeed("walking-lunges", 3, 10, 14, 90),
                TemplateExerciseSeed("calf-raise", 4, 12, 20, 60),
            ]),
            TemplateDaySeed(3, "Day 4 · Shoulders", "shoulders", [
                TemplateExerciseSeed("overhead-press", 5, 5, 8, 150, 0.74),
                TemplateExerciseSeed("seated-db-press", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("lateral-raise", 4, 12, 20, 60),
                TemplateExerciseSeed("face-pull", 4, 12, 15, 60),
            ]),
            TemplateDaySeed(4, "Day 5 · Arms", "biceps, triceps", [
                TemplateExerciseSeed("close-grip-bench", 4, 6, 8, 120, 0.72),
                TemplateExerciseSeed("triceps-pushdown", 4, 10, 15, 75),
                TemplateExerciseSeed("biceps-curl", 4, 10, 15, 75),
                TemplateExerciseSeed("hammer-curl", 4, 10, 12, 75),
            ]),
        ],
    ),
    TemplateSeed(
        slug="hybrid-athletic",
        name="Hybrid Athletic",
        level="intermediate",
        split_type="hybrid",
        days_per_week=5,
        description="Смешанный силовой и функциональный сплит с кардио-компонентом.",
        days=[
            TemplateDaySeed(0, "Day 1 · Strength Upper", "chest, back, shoulders", [
                TemplateExerciseSeed("bench-press", 5, 4, 6, 180, 0.8),
                TemplateExerciseSeed("barbell-row", 4, 5, 8, 150, 0.76),
                TemplateExerciseSeed("seated-db-press", 4, 6, 8, 120, 0.74),
            ]),
            TemplateDaySeed(1, "Day 2 · Strength Lower", "legs, glutes", [
                TemplateExerciseSeed("barbell-back-squat", 5, 4, 6, 180, 0.82),
                TemplateExerciseSeed("romanian-deadlift", 4, 6, 8, 150, 0.76),
                TemplateExerciseSeed("hip-thrust", 4, 8, 10, 120, 0.72),
            ]),
            TemplateDaySeed(2, "Day 3 · Conditioning", "full_body, cardio", [
                TemplateExerciseSeed("rowing-machine", 6, 2, 3, 60, None, "2-3 min hard intervals"),
                TemplateExerciseSeed("treadmill-run", 5, 3, 4, 60, None, "3-4 min threshold intervals"),
                TemplateExerciseSeed("plank", 4, 30, 45, 45, None, "seconds"),
            ]),
            TemplateDaySeed(3, "Day 4 · Hypertrophy Upper", "chest, back, arms", [
                TemplateExerciseSeed("incline-bench", 4, 8, 12, 120, 0.68),
                TemplateExerciseSeed("lat-pulldown", 4, 8, 12, 120, 0.68),
                TemplateExerciseSeed("face-pull", 3, 12, 15, 60),
                TemplateExerciseSeed("preacher-curl", 3, 10, 12, 75),
            ]),
            TemplateDaySeed(4, "Day 5 · Hypertrophy Lower", "legs, glutes, core", [
                TemplateExerciseSeed("leg-press", 4, 10, 12, 120, 0.68),
                TemplateExerciseSeed("walking-lunges", 4, 10, 12, 90),
                TemplateExerciseSeed("leg-curl", 3, 12, 15, 75),
                TemplateExerciseSeed("cable-crunch", 4, 12, 15, 60),
            ]),
        ],
    ),
    TemplateSeed(
        slug="custom-split-builder",
        name="Custom Split Builder",
        level="beginner",
        split_type="custom_split",
        days_per_week=4,
        description="Гибкий универсальный 4-дневный шаблон, который легко персонализировать.",
        days=[
            TemplateDaySeed(0, "Day 1 · Upper Push", "chest, shoulders, triceps", [
                TemplateExerciseSeed("bench-press", 4, 6, 10, 150, 0.72),
                TemplateExerciseSeed("seated-db-press", 4, 8, 12, 120, 0.68),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 15, 75),
            ]),
            TemplateDaySeed(1, "Day 2 · Lower", "legs, glutes", [
                TemplateExerciseSeed("barbell-back-squat", 4, 6, 10, 150, 0.74),
                TemplateExerciseSeed("leg-press", 3, 10, 12, 120, 0.68),
                TemplateExerciseSeed("calf-raise", 4, 12, 20, 60),
            ]),
            TemplateDaySeed(2, "Day 3 · Upper Pull", "back, biceps", [
                TemplateExerciseSeed("pull-up", 4, 6, 10, 120),
                TemplateExerciseSeed("barbell-row", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("biceps-curl", 3, 10, 15, 75),
            ]),
            TemplateDaySeed(3, "Day 4 · Full Body", "full_body", [
                TemplateExerciseSeed("romanian-deadlift", 4, 8, 10, 120, 0.7),
                TemplateExerciseSeed("incline-bench", 4, 8, 12, 120, 0.68),
                TemplateExerciseSeed("lat-pulldown", 3, 10, 12, 90, 0.66),
                TemplateExerciseSeed("plank", 3, 30, 45, 45, None, "seconds"),
            ]),
        ],
    ),
    TemplateSeed(
        slug="dup-strength-wave",
        name="DUP Strength Wave",
        level="advanced",
        split_type="dup",
        days_per_week=4,
        description="Ежедневная волнообразная периодизация: heavy / medium / volume / power.",
        days=[
            TemplateDaySeed(0, "Day 1 · Heavy", "strength", [
                TemplateExerciseSeed("barbell-back-squat", 5, 3, 5, 180, 0.86),
                TemplateExerciseSeed("bench-press", 5, 3, 5, 180, 0.86),
                TemplateExerciseSeed("barbell-row", 4, 5, 6, 150, 0.8),
            ]),
            TemplateDaySeed(1, "Day 2 · Medium", "strength-hypertrophy", [
                TemplateExerciseSeed("overhead-press", 4, 6, 8, 150, 0.78),
                TemplateExerciseSeed("leg-press", 4, 8, 10, 120, 0.74),
                TemplateExerciseSeed("lat-pulldown", 4, 8, 10, 120, 0.74),
            ]),
            TemplateDaySeed(2, "Day 3 · Volume", "hypertrophy", [
                TemplateExerciseSeed("incline-bench", 5, 8, 10, 120, 0.72),
                TemplateExerciseSeed("romanian-deadlift", 5, 8, 10, 150, 0.74),
                TemplateExerciseSeed("walking-lunges", 4, 10, 12, 90),
                TemplateExerciseSeed("face-pull", 4, 12, 15, 60),
            ]),
            TemplateDaySeed(3, "Day 4 · Power", "power, technique", [
                TemplateExerciseSeed("deadlift", 4, 2, 3, 180, 0.88),
                TemplateExerciseSeed("close-grip-bench", 4, 4, 6, 150, 0.82),
                TemplateExerciseSeed("pull-up", 4, 5, 8, 120),
                TemplateExerciseSeed("plank", 4, 30, 45, 45, None, "seconds"),
            ]),
        ],
    ),
]


async def ensure_seed_templates(db: AsyncSession) -> tuple[int, int]:
    exercises = (await db.execute(select(Exercise))).scalars().all()
    by_slug = {e.slug: e for e in exercises}

    existing = (
        await db.execute(
            select(WorkoutTemplate).options(
                selectinload(WorkoutTemplate.days).selectinload(TemplateDay.exercises),
            ),
        )
    ).scalars().all()
    existing_by_slug = {item.slug: item for item in existing}
    target_slugs = {item.slug for item in TEMPLATES}

    created = 0
    updated = 0
    for seed in TEMPLATES:
        template = existing_by_slug.get(seed.slug)
        if template is None:
            template = WorkoutTemplate(
                slug=seed.slug,
                name=seed.name,
                level=seed.level,
                split_type=seed.split_type,
                days_per_week=seed.days_per_week,
                description=seed.description,
                is_active=True,
            )
            db.add(template)
            await db.flush()
            created += 1
        else:
            template.name = seed.name
            template.level = seed.level
            template.split_type = seed.split_type
            template.days_per_week = seed.days_per_week
            template.description = seed.description
            template.is_active = True
            await db.execute(delete(TemplateDay).where(TemplateDay.template_id == template.id))
            await db.flush()
            updated += 1

        for day_seed in seed.days:
            day = TemplateDay(
                template_id=template.id,
                day_index=day_seed.day_index,
                title=day_seed.title,
                focus=day_seed.focus,
                is_rest=False,
            )
            db.add(day)
            await db.flush()
            for position, ex_seed in enumerate(day_seed.exercises):
                exercise = by_slug.get(ex_seed.slug)
                if exercise is None:
                    continue
                db.add(
                    TemplateExercise(
                        template_day_id=day.id,
                        exercise_id=exercise.id,
                        position=position,
                        sets=ex_seed.sets,
                        reps_min=ex_seed.reps_min,
                        reps_max=ex_seed.reps_max,
                        rest_sec=ex_seed.rest_sec,
                        target_percent_1rm=ex_seed.target_percent_1rm,
                        notes=ex_seed.notes,
                    ),
                )

    for stale in existing:
        if stale.slug not in target_slugs:
            stale.is_active = False

    await db.commit()
    return created, updated
