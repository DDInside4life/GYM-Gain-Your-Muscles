"""Idempotent exercise seeder. Run as: python -m app.data.seed_exercises"""
from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.exercise import Equipment, Exercise, ExerciseCategory, MuscleGroup

SEED: list[dict] = [
    {
        "slug": "barbell-back-squat", "name": "Barbell Back Squat",
        "description": "King of leg exercises. Develops quads, glutes and posterior chain.",
        "primary_muscle": MuscleGroup.legs,
        "secondary_muscles": ["glutes", "core", "back"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 4,
        "contraindications": ["knee", "deep_squat", "spine_load"],
    },
    {
        "slug": "goblet-squat", "name": "Goblet Squat",
        "description": "Front-loaded squat variation. Beginner-friendly.",
        "primary_muscle": MuscleGroup.legs,
        "secondary_muscles": ["glutes", "core"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": ["knee"],
    },
    {
        "slug": "romanian-deadlift", "name": "Romanian Deadlift",
        "description": "Hip-hinge movement targeting glutes and hamstrings.",
        "primary_muscle": MuscleGroup.glutes,
        "secondary_muscles": ["back", "legs"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 3, "contraindications": ["spine_load", "heavy_deadlift"],
    },
    {
        "slug": "leg-press", "name": "Leg Press",
        "description": "Machine compound for quads and glutes with low spine load.",
        "primary_muscle": MuscleGroup.legs, "secondary_muscles": ["glutes"],
        "equipment": Equipment.machine, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": ["knee"],
    },
    {
        "slug": "walking-lunges", "name": "Walking Lunges",
        "description": "Unilateral quad/glute builder.",
        "primary_muscle": MuscleGroup.legs, "secondary_muscles": ["glutes", "core"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.compound,
        "difficulty": 3, "contraindications": ["knee"],
    },
    {
        "slug": "hip-thrust", "name": "Barbell Hip Thrust",
        "description": "Glute-dominant bridge movement.",
        "primary_muscle": MuscleGroup.glutes, "secondary_muscles": ["legs"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 3, "contraindications": [],
    },
    {
        "slug": "standing-calf-raise", "name": "Standing Calf Raise",
        "description": "Isolation for gastrocnemius.",
        "primary_muscle": MuscleGroup.calves, "secondary_muscles": [],
        "equipment": Equipment.machine, "category": ExerciseCategory.isolation,
        "difficulty": 1, "contraindications": [],
    },
    {
        "slug": "bench-press", "name": "Barbell Bench Press",
        "description": "Classic horizontal press for chest mass and strength.",
        "primary_muscle": MuscleGroup.chest, "secondary_muscles": ["triceps", "shoulders"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 3, "contraindications": ["shoulder", "bench_heavy"],
    },
    {
        "slug": "dumbbell-bench-press", "name": "Dumbbell Bench Press",
        "description": "Chest press with a larger range of motion than the barbell.",
        "primary_muscle": MuscleGroup.chest, "secondary_muscles": ["triceps"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": ["shoulder"],
    },
    {
        "slug": "incline-dumbbell-press", "name": "Incline Dumbbell Press",
        "description": "Upper chest emphasis.",
        "primary_muscle": MuscleGroup.chest, "secondary_muscles": ["shoulders", "triceps"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": ["shoulder"],
    },
    {
        "slug": "push-up", "name": "Push-Up",
        "description": "Bodyweight horizontal press.",
        "primary_muscle": MuscleGroup.chest, "secondary_muscles": ["triceps", "core"],
        "equipment": Equipment.bodyweight, "category": ExerciseCategory.compound,
        "difficulty": 1, "contraindications": ["wrist"],
    },
    {
        "slug": "cable-fly", "name": "Cable Chest Fly",
        "description": "Stretch-focused isolation for pecs.",
        "primary_muscle": MuscleGroup.chest, "secondary_muscles": [],
        "equipment": Equipment.cable, "category": ExerciseCategory.isolation,
        "difficulty": 2, "contraindications": ["shoulder"],
    },
    {
        "slug": "pull-up", "name": "Pull-Up",
        "description": "Vertical pull, lat-dominant.",
        "primary_muscle": MuscleGroup.back, "secondary_muscles": ["biceps", "core"],
        "equipment": Equipment.bodyweight, "category": ExerciseCategory.compound,
        "difficulty": 4, "contraindications": ["elbow", "shoulder"],
    },
    {
        "slug": "lat-pulldown", "name": "Lat Pulldown",
        "description": "Machine vertical pull.",
        "primary_muscle": MuscleGroup.back, "secondary_muscles": ["biceps"],
        "equipment": Equipment.cable, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": [],
    },
    {
        "slug": "barbell-row", "name": "Barbell Row",
        "description": "Heavy horizontal pull for back thickness.",
        "primary_muscle": MuscleGroup.back, "secondary_muscles": ["biceps", "forearms"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 4, "contraindications": ["spine_load", "back"],
    },
    {
        "slug": "dumbbell-row", "name": "Single-Arm Dumbbell Row",
        "description": "Unilateral back row.",
        "primary_muscle": MuscleGroup.back, "secondary_muscles": ["biceps"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": [],
    },
    {
        "slug": "face-pull", "name": "Face Pull",
        "description": "Rear-delt and upper back accessory.",
        "primary_muscle": MuscleGroup.shoulders, "secondary_muscles": ["back"],
        "equipment": Equipment.cable, "category": ExerciseCategory.isolation,
        "difficulty": 1, "contraindications": [],
    },
    {
        "slug": "overhead-press", "name": "Standing Overhead Press",
        "description": "Vertical press for shoulders.",
        "primary_muscle": MuscleGroup.shoulders, "secondary_muscles": ["triceps", "core"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 4, "contraindications": ["overhead_press", "shoulder"],
    },
    {
        "slug": "dumbbell-shoulder-press", "name": "Seated Dumbbell Shoulder Press",
        "description": "Shoulder press with neutral grip option.",
        "primary_muscle": MuscleGroup.shoulders, "secondary_muscles": ["triceps"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.compound,
        "difficulty": 2, "contraindications": ["shoulder"],
    },
    {
        "slug": "lateral-raise", "name": "Lateral Raise",
        "description": "Side-delt isolation.",
        "primary_muscle": MuscleGroup.shoulders, "secondary_muscles": [],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.isolation,
        "difficulty": 1, "contraindications": [],
    },
    {
        "slug": "barbell-curl", "name": "Barbell Curl",
        "description": "Classic biceps builder.",
        "primary_muscle": MuscleGroup.biceps, "secondary_muscles": ["forearms"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.isolation,
        "difficulty": 2, "contraindications": ["wrist", "elbow"],
    },
    {
        "slug": "hammer-curl", "name": "Hammer Curl",
        "description": "Brachialis-focused curl.",
        "primary_muscle": MuscleGroup.biceps, "secondary_muscles": ["forearms"],
        "equipment": Equipment.dumbbell, "category": ExerciseCategory.isolation,
        "difficulty": 1, "contraindications": ["elbow"],
    },
    {
        "slug": "triceps-pushdown", "name": "Triceps Pushdown",
        "description": "Cable triceps isolation.",
        "primary_muscle": MuscleGroup.triceps, "secondary_muscles": [],
        "equipment": Equipment.cable, "category": ExerciseCategory.isolation,
        "difficulty": 1, "contraindications": ["elbow"],
    },
    {
        "slug": "close-grip-bench", "name": "Close-Grip Bench Press",
        "description": "Compound triceps focus.",
        "primary_muscle": MuscleGroup.triceps, "secondary_muscles": ["chest", "shoulders"],
        "equipment": Equipment.barbell, "category": ExerciseCategory.compound,
        "difficulty": 3, "contraindications": ["wrist", "heavy_press"],
    },
    {
        "slug": "plank", "name": "Plank",
        "description": "Isometric core hold.",
        "primary_muscle": MuscleGroup.core, "secondary_muscles": ["shoulders"],
        "equipment": Equipment.bodyweight, "category": ExerciseCategory.isolation,
        "difficulty": 1, "contraindications": [],
    },
    {
        "slug": "hanging-leg-raise", "name": "Hanging Leg Raise",
        "description": "Lower abs dominant.",
        "primary_muscle": MuscleGroup.core, "secondary_muscles": [],
        "equipment": Equipment.bodyweight, "category": ExerciseCategory.isolation,
        "difficulty": 3, "contraindications": ["back"],
    },
    {
        "slug": "cable-crunch", "name": "Cable Crunch",
        "description": "Loaded spinal flexion.",
        "primary_muscle": MuscleGroup.core, "secondary_muscles": [],
        "equipment": Equipment.cable, "category": ExerciseCategory.isolation,
        "difficulty": 2, "contraindications": ["spine_load"],
    },
    {
        "slug": "kettlebell-swing", "name": "Kettlebell Swing",
        "description": "Explosive posterior-chain and cardio hybrid.",
        "primary_muscle": MuscleGroup.glutes, "secondary_muscles": ["back", "cardio"],
        "equipment": Equipment.kettlebell, "category": ExerciseCategory.compound,
        "difficulty": 3, "contraindications": ["spine_load", "back"],
    },
    {
        "slug": "rowing-machine", "name": "Rowing Machine",
        "description": "Full-body cardio.",
        "primary_muscle": MuscleGroup.cardio, "secondary_muscles": ["back", "legs"],
        "equipment": Equipment.machine, "category": ExerciseCategory.cardio,
        "difficulty": 1, "contraindications": [],
    },
    {
        "slug": "treadmill-run", "name": "Treadmill Run",
        "description": "Cardio — steady state or intervals.",
        "primary_muscle": MuscleGroup.cardio, "secondary_muscles": ["legs"],
        "equipment": Equipment.machine, "category": ExerciseCategory.cardio,
        "difficulty": 1, "contraindications": ["knee"],
    },
]


async def run() -> None:
    async with SessionLocal() as db:
        existing = {row for row in (await db.execute(select(Exercise.slug))).scalars().all()}
        created = 0
        for data in SEED:
            if data["slug"] in existing:
                continue
            db.add(Exercise(**data))
            created += 1
        await db.commit()
        print(f"[seed] exercises created: {created}; total seeded: {len(SEED)}")


if __name__ == "__main__":
    asyncio.run(run())
