"""Predefined monthly workout templates (4-week structures, in Russian).

The previous version stored seven English-named templates that drove an
auto-weight estimator. We deliberately moved to a simpler model:

* Five clean, opinionated templates (full-body / upper-lower / PPL /
  strength / hypertrophy)
* Russian names and notes (UI is Russian)
* No ``target_percent_1rm`` and no auto-weight: the user fills the
  working weight in the plan view manually
* Templates store a single training week — the generator clones it into
  the requested number of weeks (default 4)

The seed function is idempotent: rerunning it updates titles, sets/reps
and rest, drops removed templates and never duplicates rows.
"""
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
        slug="full-body-3",
        name="Фулбади (3 раза в неделю)",
        level="beginner",
        split_type="full_body",
        days_per_week=3,
        description=(
            "Простая полнотельная программа на 4 недели. Подходит новичкам и тем, "
            "кто возвращается к тренировкам. Каждый день прорабатываются крупные "
            "мышечные группы базовыми движениями."
        ),
        days=[
            TemplateDaySeed(0, "День 1 · Фулбади A", "ноги, грудь, спина", [
                TemplateExerciseSeed("barbell-back-squat", 3, 8, 10, 120),
                TemplateExerciseSeed("bench-press", 3, 8, 10, 120),
                TemplateExerciseSeed("barbell-row", 3, 8, 10, 90),
                TemplateExerciseSeed("plank", 3, 30, 45, 60, "Удержание, сек."),
            ]),
            TemplateDaySeed(1, "День 2 · Фулбади B", "ноги, плечи, спина", [
                TemplateExerciseSeed("leg-press", 3, 10, 12, 90),
                TemplateExerciseSeed("seated-db-press", 3, 8, 12, 90),
                TemplateExerciseSeed("lat-pulldown", 3, 10, 12, 90),
                TemplateExerciseSeed("hanging-leg-raise", 3, 8, 12, 60),
            ]),
            TemplateDaySeed(2, "День 3 · Фулбади C", "тяга, грудь, руки", [
                TemplateExerciseSeed("romanian-deadlift", 3, 8, 10, 120),
                TemplateExerciseSeed("incline-bench", 3, 8, 10, 90),
                TemplateExerciseSeed("pull-up", 3, 6, 10, 90),
                TemplateExerciseSeed("biceps-curl", 3, 10, 12, 60),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 12, 60),
            ]),
        ],
    ),
    TemplateSeed(
        slug="upper-lower-4",
        name="Верх / Низ (4 раза в неделю)",
        level="intermediate",
        split_type="upper_lower",
        days_per_week=4,
        description=(
            "Классический сплит верх/низ с двумя верхними и двумя нижними тренировками. "
            "Сбалансированная нагрузка для роста силы и массы за 4 недели."
        ),
        days=[
            TemplateDaySeed(0, "День 1 · Верх A", "грудь, спина, плечи", [
                TemplateExerciseSeed("bench-press", 4, 6, 8, 150),
                TemplateExerciseSeed("barbell-row", 4, 8, 10, 120),
                TemplateExerciseSeed("seated-db-press", 3, 8, 10, 90),
                TemplateExerciseSeed("biceps-curl", 3, 10, 12, 60),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 12, 60),
            ]),
            TemplateDaySeed(1, "День 2 · Низ A", "ноги, ягодицы", [
                TemplateExerciseSeed("barbell-back-squat", 4, 6, 8, 150),
                TemplateExerciseSeed("romanian-deadlift", 4, 8, 10, 120),
                TemplateExerciseSeed("leg-extension", 3, 12, 15, 60),
                TemplateExerciseSeed("leg-curl", 3, 12, 15, 60),
                TemplateExerciseSeed("calf-raise", 3, 12, 15, 60),
            ]),
            TemplateDaySeed(2, "День 3 · Верх B", "грудь, спина, руки", [
                TemplateExerciseSeed("incline-bench", 4, 8, 10, 120),
                TemplateExerciseSeed("lat-pulldown", 4, 8, 10, 90),
                TemplateExerciseSeed("close-grip-bench", 3, 8, 10, 90),
                TemplateExerciseSeed("face-pull", 3, 12, 15, 60),
                TemplateExerciseSeed("hammer-curl", 3, 10, 12, 60),
            ]),
            TemplateDaySeed(3, "День 4 · Низ B", "ноги, ягодицы, кор", [
                TemplateExerciseSeed("leg-press", 4, 8, 12, 120),
                TemplateExerciseSeed("hip-thrust", 4, 8, 10, 90),
                TemplateExerciseSeed("walking-lunges", 3, 10, 12, 90),
                TemplateExerciseSeed("cable-crunch", 3, 12, 15, 60),
            ]),
        ],
    ),
    TemplateSeed(
        slug="push-pull-legs-6",
        name="Push Pull Legs (6 дней)",
        level="intermediate",
        split_type="ppl",
        days_per_week=6,
        description=(
            "Сплит из шести тренировок: толкающая, тянущая и ноги, повторённые дважды. "
            "Подходит для опытных, готовых к высокой частоте и объёму."
        ),
        days=[
            TemplateDaySeed(0, "День 1 · Push A", "грудь, плечи, трицепс", [
                TemplateExerciseSeed("bench-press", 4, 6, 8, 150),
                TemplateExerciseSeed("incline-bench", 4, 8, 10, 120),
                TemplateExerciseSeed("seated-db-press", 3, 8, 10, 90),
                TemplateExerciseSeed("triceps-pushdown", 3, 10, 12, 60),
            ]),
            TemplateDaySeed(1, "День 2 · Pull A", "спина, бицепс", [
                TemplateExerciseSeed("deadlift", 3, 4, 6, 180),
                TemplateExerciseSeed("pull-up", 4, 6, 10, 120),
                TemplateExerciseSeed("barbell-row", 4, 8, 10, 90),
                TemplateExerciseSeed("hammer-curl", 3, 10, 12, 60),
            ]),
            TemplateDaySeed(2, "День 3 · Legs A", "ноги, ягодицы, икры", [
                TemplateExerciseSeed("barbell-back-squat", 4, 6, 8, 150),
                TemplateExerciseSeed("leg-press", 4, 10, 12, 120),
                TemplateExerciseSeed("romanian-deadlift", 4, 8, 10, 120),
                TemplateExerciseSeed("calf-raise", 4, 12, 15, 60),
            ]),
            TemplateDaySeed(3, "День 4 · Push B", "грудь, плечи, трицепс", [
                TemplateExerciseSeed("close-grip-bench", 4, 6, 8, 120),
                TemplateExerciseSeed("db-fly", 3, 12, 15, 60),
                TemplateExerciseSeed("lateral-raise", 4, 12, 15, 60),
                TemplateExerciseSeed("dips", 3, 8, 12, 90),
            ]),
            TemplateDaySeed(4, "День 5 · Pull B", "спина, задние дельты, бицепс", [
                TemplateExerciseSeed("lat-pulldown", 4, 8, 10, 90),
                TemplateExerciseSeed("seated-row-machine", 4, 8, 10, 90),
                TemplateExerciseSeed("face-pull", 4, 12, 15, 60),
                TemplateExerciseSeed("preacher-curl", 3, 10, 12, 60),
            ]),
            TemplateDaySeed(5, "День 6 · Legs B", "ноги, ягодицы", [
                TemplateExerciseSeed("hip-thrust", 4, 8, 10, 90),
                TemplateExerciseSeed("bulgarian-split-squat", 3, 10, 12, 90),
                TemplateExerciseSeed("leg-extension", 3, 12, 15, 60),
                TemplateExerciseSeed("leg-curl", 3, 12, 15, 60),
            ]),
        ],
    ),
    TemplateSeed(
        slug="strength-3-4",
        name="Силовая программа (3–4 дня)",
        level="intermediate",
        split_type="strength",
        days_per_week=3,
        description=(
            "Базовая силовая программа из 3–4 тренировок в неделю. Малое число повторений, "
            "длительный отдых и фокус на технике в приседе, жиме и тяге."
        ),
        days=[
            TemplateDaySeed(0, "День 1 · Сила A", "присед, жим, тяга", [
                TemplateExerciseSeed("barbell-back-squat", 5, 4, 6, 180),
                TemplateExerciseSeed("bench-press", 5, 4, 6, 180),
                TemplateExerciseSeed("barbell-row", 4, 5, 6, 150),
                TemplateExerciseSeed("plank", 3, 30, 45, 60, "Удержание, сек."),
            ]),
            TemplateDaySeed(1, "День 2 · Сила B", "тяга, жим стоя, корпус", [
                TemplateExerciseSeed("deadlift", 4, 3, 5, 210),
                TemplateExerciseSeed("overhead-press", 4, 5, 6, 150),
                TemplateExerciseSeed("pull-up", 4, 5, 8, 120),
                TemplateExerciseSeed("hanging-leg-raise", 3, 8, 12, 60),
            ]),
            TemplateDaySeed(2, "День 3 · Сила C", "присед, жим, ассистенция", [
                TemplateExerciseSeed("front-squat", 4, 5, 6, 150),
                TemplateExerciseSeed("incline-bench", 4, 5, 6, 150),
                TemplateExerciseSeed("romanian-deadlift", 3, 6, 8, 120),
                TemplateExerciseSeed("close-grip-bench", 3, 6, 8, 120),
            ]),
        ],
    ),
    TemplateSeed(
        slug="hypertrophy-5",
        name="Гипертрофия (4–5 дней)",
        level="intermediate",
        split_type="hypertrophy",
        days_per_week=5,
        description=(
            "Программа на гипертрофию: умеренный вес, средний диапазон повторений и большое "
            "число рабочих подходов. Каждая мышечная группа получает отдельный тренировочный день."
        ),
        days=[
            TemplateDaySeed(0, "День 1 · Грудь", "грудь", [
                TemplateExerciseSeed("bench-press", 4, 8, 10, 90),
                TemplateExerciseSeed("incline-bench", 4, 8, 10, 90),
                TemplateExerciseSeed("db-fly", 3, 12, 15, 60),
                TemplateExerciseSeed("push-up", 3, 12, 20, 60),
            ]),
            TemplateDaySeed(1, "День 2 · Спина", "спина", [
                TemplateExerciseSeed("pull-up", 4, 6, 10, 90),
                TemplateExerciseSeed("barbell-row", 4, 8, 10, 90),
                TemplateExerciseSeed("lat-pulldown", 3, 10, 12, 60),
                TemplateExerciseSeed("seated-row-machine", 3, 10, 12, 60),
            ]),
            TemplateDaySeed(2, "День 3 · Ноги", "ноги, ягодицы", [
                TemplateExerciseSeed("barbell-back-squat", 4, 8, 10, 120),
                TemplateExerciseSeed("leg-press", 4, 10, 12, 90),
                TemplateExerciseSeed("walking-lunges", 3, 10, 12, 90),
                TemplateExerciseSeed("calf-raise", 4, 12, 15, 60),
            ]),
            TemplateDaySeed(3, "День 4 · Плечи", "плечи", [
                TemplateExerciseSeed("overhead-press", 4, 8, 10, 90),
                TemplateExerciseSeed("seated-db-press", 4, 8, 10, 90),
                TemplateExerciseSeed("lateral-raise", 4, 12, 15, 60),
                TemplateExerciseSeed("face-pull", 3, 12, 15, 60),
            ]),
            TemplateDaySeed(4, "День 5 · Руки", "бицепс, трицепс", [
                TemplateExerciseSeed("close-grip-bench", 4, 8, 10, 90),
                TemplateExerciseSeed("triceps-pushdown", 4, 10, 12, 60),
                TemplateExerciseSeed("biceps-curl", 4, 10, 12, 60),
                TemplateExerciseSeed("hammer-curl", 3, 10, 12, 60),
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
                        target_percent_1rm=None,
                        notes=ex_seed.notes,
                    ),
                )

    for stale in existing:
        if stale.slug not in target_slugs:
            stale.is_active = False

    await db.commit()
    return created, updated
