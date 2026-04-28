"""Idempotent exercise seeder. Run as: python -m app.data.seed_exercises"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.data.seed_templates import ensure_seed_templates
from app.models.exercise import Equipment, Exercise, ExerciseCategory, MuscleGroup


def ex(
    slug: str,
    name_ru: str,
    name_en: str,
    primary: MuscleGroup,
    equipment: Equipment,
    category: ExerciseCategory,
    difficulty: int,
    description: str,
    *,
    archetype: str = "generic",
    is_home: bool = True,
    is_gym: bool = True,
    suitable_for_test: bool = False,
    suitable_for_progression: bool = True,
    secondary: list[str] | None = None,
    contraindications: list[str] | None = None,
) -> dict:
    return {
        "slug": slug,
        "name_ru": name_ru,
        "name_en": name_en,
        "name": name_ru,
        "description": description,
        "primary_muscle": primary,
        "secondary_muscles": secondary or [],
        "equipment": equipment,
        "category": category,
        "difficulty": difficulty,
        "contraindications": contraindications or [],
        "movement_archetype": archetype,
        "is_home": is_home,
        "is_gym": is_gym,
        "suitable_for_test": suitable_for_test,
        "suitable_for_progression": suitable_for_progression,
    }


SEED: list[dict] = [
    # --- грудь ---
    ex("bench-press", "Жим штанги лёжа", "Barbell Bench Press",
       MuscleGroup.chest, Equipment.barbell, ExerciseCategory.compound, 3,
       "Базовое силовое упражнение для груди.",
       archetype="bench_press_barbell", is_home=False, suitable_for_test=True,
       secondary=["triceps", "shoulders"], contraindications=["bench_heavy", "shoulder"]),
    ex("incline-bench", "Жим штанги на наклонной", "Incline Bench Press",
       MuscleGroup.chest, Equipment.barbell, ExerciseCategory.compound, 3,
       "Жим под углом 30°: акцент на верх груди.",
       archetype="incline_bench_barbell", is_home=False, suitable_for_test=True,
       secondary=["shoulders", "triceps"], contraindications=["bench_heavy", "shoulder"]),
    ex("db-bench-press", "Жим гантелей лёжа", "Dumbbell Bench Press",
       MuscleGroup.chest, Equipment.dumbbell, ExerciseCategory.compound, 2,
       "Жим гантелей с большей амплитудой и контролем плечевых суставов.",
       archetype="dumbbell_compound", suitable_for_test=True,
       secondary=["triceps", "shoulders"]),
    ex("db-fly", "Разведения гантелей лёжа", "Dumbbell Fly",
       MuscleGroup.chest, Equipment.dumbbell, ExerciseCategory.isolation, 2,
       "Изолированная работа на грудные мышцы.",
       archetype="dumbbell_isolation"),
    ex("push-up", "Отжимания от пола", "Push-Up",
       MuscleGroup.chest, Equipment.bodyweight, ExerciseCategory.compound, 1,
       "Базовое упражнение с собственным весом.",
       archetype="bodyweight_main", suitable_for_test=True),
    ex("dips", "Отжимания на брусьях", "Dips",
       MuscleGroup.chest, Equipment.bodyweight, ExerciseCategory.compound, 3,
       "Грудь и трицепс. Контроль глубины опускания.",
       archetype="bodyweight_main", suitable_for_test=True,
       contraindications=["shoulder", "wrist"]),

    # --- спина ---
    ex("deadlift", "Становая тяга", "Deadlift",
       MuscleGroup.back, Equipment.barbell, ExerciseCategory.compound, 5,
       "Силовое упражнение для всей задней цепи.",
       archetype="deadlift_barbell", is_home=False, suitable_for_test=True,
       secondary=["legs", "glutes"], contraindications=["heavy_deadlift", "spine_load", "back"]),
    ex("barbell-row", "Тяга штанги в наклоне", "Barbell Row",
       MuscleGroup.back, Equipment.barbell, ExerciseCategory.compound, 4,
       "Горизонтальная тяга для толщины спины.",
       archetype="barbell_row", is_home=False, suitable_for_test=True,
       secondary=["biceps"], contraindications=["spine_load", "back"]),
    ex("pull-up", "Подтягивания", "Pull-Up",
       MuscleGroup.back, Equipment.bodyweight, ExerciseCategory.compound, 4,
       "Вертикальная тяга собственным весом.",
       archetype="bodyweight_main", suitable_for_test=True,
       secondary=["biceps"]),
    ex("lat-pulldown", "Тяга верхнего блока", "Lat Pulldown",
       MuscleGroup.back, Equipment.cable, ExerciseCategory.compound, 2,
       "Вертикальная тяга в тренажёре.",
       archetype="machine_compound", is_home=False, suitable_for_test=True,
       secondary=["biceps"]),
    ex("seated-row-machine", "Горизонтальная тяга в тренажёре", "Seated Cable Row",
       MuscleGroup.back, Equipment.cable, ExerciseCategory.compound, 2,
       "Безопасная горизонтальная тяга для спины.",
       archetype="machine_compound", is_home=False),

    # --- ноги/ягодицы ---
    ex("barbell-back-squat", "Приседания со штангой", "Barbell Back Squat",
       MuscleGroup.legs, Equipment.barbell, ExerciseCategory.compound, 4,
       "Базовое упражнение для ног и ягодиц.",
       archetype="back_squat_barbell", is_home=False, suitable_for_test=True,
       secondary=["glutes", "core"],
       contraindications=["deep_squat", "knee", "spine_load"]),
    ex("front-squat", "Фронтальные приседания", "Front Squat",
       MuscleGroup.legs, Equipment.barbell, ExerciseCategory.compound, 4,
       "Приседания с грифом на груди: вертикальная спина.",
       archetype="back_squat_barbell", is_home=False, suitable_for_test=True,
       contraindications=["deep_squat", "knee", "wrist"]),
    ex("leg-press", "Жим ногами", "Leg Press",
       MuscleGroup.legs, Equipment.machine, ExerciseCategory.compound, 2,
       "Силовая работа ног в тренажёре.",
       archetype="leg_press_machine", is_home=False, suitable_for_test=True,
       contraindications=["knee"]),
    ex("bulgarian-split-squat", "Болгарские выпады", "Bulgarian Split Squat",
       MuscleGroup.legs, Equipment.dumbbell, ExerciseCategory.compound, 3,
       "Одноногая работа на силу и баланс.",
       archetype="dumbbell_compound",
       contraindications=["knee"]),
    ex("walking-lunges", "Выпады с гантелями", "Walking Lunges",
       MuscleGroup.legs, Equipment.dumbbell, ExerciseCategory.compound, 3,
       "Функциональная работа ног.",
       archetype="dumbbell_compound",
       contraindications=["knee"]),
    ex("leg-extension", "Разгибания ног", "Leg Extension",
       MuscleGroup.legs, Equipment.machine, ExerciseCategory.isolation, 1,
       "Изоляция квадрицепса.",
       archetype="machine_isolation", is_home=False,
       contraindications=["knee"]),
    ex("leg-curl", "Сгибания ног лёжа", "Leg Curl",
       MuscleGroup.legs, Equipment.machine, ExerciseCategory.isolation, 1,
       "Изоляция бицепса бедра.",
       archetype="machine_isolation", is_home=False),
    ex("romanian-deadlift", "Румынская тяга", "Romanian Deadlift",
       MuscleGroup.glutes, Equipment.barbell, ExerciseCategory.compound, 3,
       "Задняя поверхность бедра и ягодицы.",
       archetype="romanian_deadlift_barbell", is_home=False, suitable_for_test=True,
       secondary=["back"], contraindications=["spine_load", "back"]),
    ex("hip-thrust", "Ягодичный мост со штангой", "Barbell Hip Thrust",
       MuscleGroup.glutes, Equipment.barbell, ExerciseCategory.compound, 3,
       "Акцентированная работа ягодиц.",
       archetype="hip_thrust_barbell", is_home=False, suitable_for_test=True),
    ex("calf-raise", "Подъёмы на икры", "Calf Raise",
       MuscleGroup.calves, Equipment.machine, ExerciseCategory.isolation, 1,
       "Изоляция икроножных мышц.",
       archetype="machine_isolation", is_home=False),
    ex("standing-calf-bw", "Подъёмы на носки стоя (свой вес)", "Bodyweight Calf Raise",
       MuscleGroup.calves, Equipment.bodyweight, ExerciseCategory.isolation, 1,
       "Икры с собственным весом — для дома.",
       archetype="bodyweight_main"),

    # --- плечи ---
    ex("overhead-press", "Жим штанги стоя", "Overhead Press",
       MuscleGroup.shoulders, Equipment.barbell, ExerciseCategory.compound, 4,
       "Базовый вертикальный жим.",
       archetype="overhead_press_barbell", is_home=False, suitable_for_test=True,
       contraindications=["overhead_press", "shoulder"]),
    ex("seated-db-press", "Жим гантелей сидя", "Seated Dumbbell Press",
       MuscleGroup.shoulders, Equipment.dumbbell, ExerciseCategory.compound, 2,
       "Жим для дельт в стабильном положении.",
       archetype="dumbbell_compound", suitable_for_test=True,
       contraindications=["overhead_press", "shoulder"]),
    ex("lateral-raise", "Подъёмы гантелей в стороны", "Lateral Raise",
       MuscleGroup.shoulders, Equipment.dumbbell, ExerciseCategory.isolation, 1,
       "Средние дельты.",
       archetype="dumbbell_isolation"),
    ex("face-pull", "Тяга каната к лицу", "Face Pull",
       MuscleGroup.shoulders, Equipment.cable, ExerciseCategory.isolation, 1,
       "Задние дельты и ротаторы.",
       archetype="cable_isolation", is_home=False),

    # --- руки ---
    ex("biceps-curl", "Сгибания на бицепс", "Biceps Curl",
       MuscleGroup.biceps, Equipment.dumbbell, ExerciseCategory.isolation, 1,
       "Классическое упражнение на бицепс.",
       archetype="dumbbell_isolation"),
    ex("hammer-curl", "Молотковые сгибания", "Hammer Curl",
       MuscleGroup.biceps, Equipment.dumbbell, ExerciseCategory.isolation, 1,
       "Брахиалис и предплечья.",
       archetype="dumbbell_isolation"),
    ex("preacher-curl", "Сгибания на скамье Скотта", "Preacher Curl",
       MuscleGroup.biceps, Equipment.machine, ExerciseCategory.isolation, 2,
       "Контролируемая работа на бицепс.",
       archetype="machine_isolation", is_home=False),
    ex("triceps-pushdown", "Разгибание рук на блоке", "Triceps Pushdown",
       MuscleGroup.triceps, Equipment.cable, ExerciseCategory.isolation, 1,
       "Изоляция трицепса.",
       archetype="cable_isolation", is_home=False),
    ex("close-grip-bench", "Жим штанги узким хватом", "Close-Grip Bench Press",
       MuscleGroup.triceps, Equipment.barbell, ExerciseCategory.compound, 3,
       "Силовой акцент на трицепс.",
       archetype="bench_press_barbell", is_home=False, suitable_for_test=True),

    # --- кор ---
    ex("plank", "Планка", "Plank",
       MuscleGroup.core, Equipment.bodyweight, ExerciseCategory.isolation, 1,
       "Статическое упражнение на корпус.",
       archetype="bodyweight_main", suitable_for_progression=False),
    ex("hanging-leg-raise", "Подъём ног в висе", "Hanging Leg Raise",
       MuscleGroup.core, Equipment.bodyweight, ExerciseCategory.isolation, 3,
       "Нижний пресс.",
       archetype="bodyweight_main"),
    ex("cable-crunch", "Скручивания на блоке", "Cable Crunch",
       MuscleGroup.core, Equipment.cable, ExerciseCategory.isolation, 2,
       "Силовая работа пресса.",
       archetype="cable_isolation", is_home=False),

    # --- кардио ---
    ex("rowing-machine", "Гребной тренажёр", "Rowing Machine",
       MuscleGroup.cardio, Equipment.machine, ExerciseCategory.cardio, 1,
       "Кардио на всё тело.",
       archetype="cardio", is_home=False, suitable_for_progression=False),
    ex("treadmill-run", "Бег на дорожке", "Treadmill Run",
       MuscleGroup.cardio, Equipment.machine, ExerciseCategory.cardio, 1,
       "Кардионагрузка в устойчивом темпе.",
       archetype="cardio", is_home=False, suitable_for_progression=False),
    ex("jump-rope", "Прыжки на скакалке", "Jump Rope",
       MuscleGroup.cardio, Equipment.bodyweight, ExerciseCategory.cardio, 1,
       "Кардио высокой интенсивности дома.",
       archetype="cardio", suitable_for_progression=False,
       contraindications=["knee", "ankle", "high_impact"]),
]


async def run() -> None:
    async with SessionLocal() as db:
        existing = {
            row.slug: row
            for row in (
                await db.execute(select(Exercise))
            ).scalars().all()
        }
        target_slugs = {item["slug"] for item in SEED}
        created = 0
        updated = 0
        for data in SEED:
            row = existing.get(data["slug"])
            if row is not None:
                for key, value in data.items():
                    setattr(row, key, value)
                row.is_active = True
                updated += 1
                continue
            db.add(Exercise(**data))
            created += 1
        for slug, row in existing.items():
            if slug not in target_slugs:
                row.is_active = False
        await db.commit()
        templates_created, templates_updated = await ensure_seed_templates(db)
        print(f"[seed] exercises created: {created}; updated: {updated}; total seeded: {len(SEED)}")
        print(f"[seed] templates created: {templates_created}; updated: {templates_updated}")


if __name__ == "__main__":
    asyncio.run(run())
