"""Idempotent exercise seeder. Run as: python -m app.data.seed_exercises"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
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
    secondary: list[str] | None = None,
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
        "contraindications": [],
    }


SEED: list[dict] = [
    ex("bench-press", "Жим лежа", "Barbell Bench Press", MuscleGroup.chest, Equipment.barbell, ExerciseCategory.compound, 3, "Базовое силовое упражнение для груди.", ["triceps", "shoulders"]),
    ex("barbell-back-squat", "Приседания со штангой", "Barbell Back Squat", MuscleGroup.legs, Equipment.barbell, ExerciseCategory.compound, 4, "Базовое упражнение для ног и ягодиц.", ["glutes", "core"]),
    ex("deadlift", "Становая тяга", "Deadlift", MuscleGroup.back, Equipment.barbell, ExerciseCategory.compound, 5, "Силовое упражнение для всей задней цепи.", ["legs", "glutes"]),
    ex("pull-up", "Подтягивания", "Pull-Up", MuscleGroup.back, Equipment.bodyweight, ExerciseCategory.compound, 4, "Вертикальная тяга собственным весом.", ["biceps"]),
    ex("seated-db-press", "Жим гантелей сидя", "Seated Dumbbell Press", MuscleGroup.shoulders, Equipment.dumbbell, ExerciseCategory.compound, 2, "Жим для дельт в стабильном положении."),
    ex("barbell-row", "Тяга штанги в наклоне", "Barbell Row", MuscleGroup.back, Equipment.barbell, ExerciseCategory.compound, 4, "Горизонтальная тяга для толщины спины.", ["biceps"]),
    ex("db-fly", "Разведения гантелей лежа", "Dumbbell Fly", MuscleGroup.chest, Equipment.dumbbell, ExerciseCategory.isolation, 2, "Изолированная работа на грудные мышцы."),
    ex("biceps-curl", "Сгибания на бицепс", "Biceps Curl", MuscleGroup.biceps, Equipment.dumbbell, ExerciseCategory.isolation, 1, "Классическое упражнение на бицепс."),
    ex("incline-bench", "Жим штанги на наклонной", "Incline Bench Press", MuscleGroup.chest, Equipment.barbell, ExerciseCategory.compound, 3, "Акцент на верх груди."),
    ex("lat-pulldown", "Тяга верхнего блока", "Lat Pulldown", MuscleGroup.back, Equipment.cable, ExerciseCategory.compound, 2, "Вертикальная тяга в тренажере.", ["biceps"]),
    ex("leg-press", "Жим ногами", "Leg Press", MuscleGroup.legs, Equipment.machine, ExerciseCategory.compound, 2, "Силовая работа ног в тренажере."),
    ex("romanian-deadlift", "Румынская тяга", "Romanian Deadlift", MuscleGroup.glutes, Equipment.barbell, ExerciseCategory.compound, 3, "Задняя поверхность бедра и ягодицы.", ["back"]),
    ex("bulgarian-split-squat", "Болгарские выпады", "Bulgarian Split Squat", MuscleGroup.legs, Equipment.dumbbell, ExerciseCategory.compound, 3, "Одноногая работа на силу и баланс."),
    ex("hip-thrust", "Ягодичный мост со штангой", "Barbell Hip Thrust", MuscleGroup.glutes, Equipment.barbell, ExerciseCategory.compound, 3, "Акцентированная работа ягодиц."),
    ex("walking-lunges", "Выпады с гантелями", "Walking Lunges", MuscleGroup.legs, Equipment.dumbbell, ExerciseCategory.compound, 3, "Функциональная работа ног."),
    ex("leg-extension", "Разгибания ног", "Leg Extension", MuscleGroup.legs, Equipment.machine, ExerciseCategory.isolation, 1, "Изоляция квадрицепса."),
    ex("leg-curl", "Сгибания ног лежа", "Leg Curl", MuscleGroup.legs, Equipment.machine, ExerciseCategory.isolation, 1, "Изоляция бицепса бедра."),
    ex("calf-raise", "Подъемы на икры", "Calf Raise", MuscleGroup.calves, Equipment.machine, ExerciseCategory.isolation, 1, "Изоляция икроножных."),
    ex("overhead-press", "Жим штанги стоя", "Overhead Press", MuscleGroup.shoulders, Equipment.barbell, ExerciseCategory.compound, 4, "Базовый вертикальный жим."),
    ex("lateral-raise", "Подъемы гантелей в стороны", "Lateral Raise", MuscleGroup.shoulders, Equipment.dumbbell, ExerciseCategory.isolation, 1, "Средние дельты."),
    ex("face-pull", "Тяга каната к лицу", "Face Pull", MuscleGroup.shoulders, Equipment.cable, ExerciseCategory.isolation, 1, "Задние дельты и ротаторы."),
    ex("triceps-pushdown", "Разгибание рук на блоке", "Triceps Pushdown", MuscleGroup.triceps, Equipment.cable, ExerciseCategory.isolation, 1, "Изоляция трицепса."),
    ex("close-grip-bench", "Жим лежа узким хватом", "Close-Grip Bench Press", MuscleGroup.triceps, Equipment.barbell, ExerciseCategory.compound, 3, "Силовой акцент на трицепс."),
    ex("hammer-curl", "Молотковые сгибания", "Hammer Curl", MuscleGroup.biceps, Equipment.dumbbell, ExerciseCategory.isolation, 1, "Брахиалис и предплечья."),
    ex("preacher-curl", "Сгибания на скамье Скотта", "Preacher Curl", MuscleGroup.biceps, Equipment.machine, ExerciseCategory.isolation, 2, "Контролируемая работа на бицепс."),
    ex("dips", "Отжимания на брусьях", "Dips", MuscleGroup.triceps, Equipment.bodyweight, ExerciseCategory.compound, 3, "Грудь и трицепс."),
    ex("push-up", "Отжимания от пола", "Push-Up", MuscleGroup.chest, Equipment.bodyweight, ExerciseCategory.compound, 1, "Базовое упражнение с собственным весом."),
    ex("plank", "Планка", "Plank", MuscleGroup.core, Equipment.bodyweight, ExerciseCategory.isolation, 1, "Статическое упражнение на корпус."),
    ex("hanging-leg-raise", "Подъем ног в висе", "Hanging Leg Raise", MuscleGroup.core, Equipment.bodyweight, ExerciseCategory.isolation, 3, "Нижний пресс."),
    ex("cable-crunch", "Скручивания на блоке", "Cable Crunch", MuscleGroup.core, Equipment.cable, ExerciseCategory.isolation, 2, "Силовая работа пресса."),
    ex("rowing-machine", "Гребной тренажер", "Rowing Machine", MuscleGroup.cardio, Equipment.machine, ExerciseCategory.cardio, 1, "Кардио на все тело."),
    ex("treadmill-run", "Бег на дорожке", "Treadmill Run", MuscleGroup.cardio, Equipment.machine, ExerciseCategory.cardio, 1, "Кардионагрузка в устойчивом темпе."),
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
        print(f"[seed] exercises created: {created}; updated: {updated}; total seeded: {len(SEED)}")


if __name__ == "__main__":
    asyncio.run(run())
