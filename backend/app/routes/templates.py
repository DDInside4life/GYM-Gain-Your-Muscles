from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import DbSession
from app.schemas.template import WorkoutTemplateRead
from app.services.workout import TemplateProgramService

router = APIRouter()


@router.get("", response_model=list[WorkoutTemplateRead])
async def list_templates(db: DbSession) -> list[WorkoutTemplateRead]:
    """Read-only template catalog. Materialization always flows through the
    questionnaire-driven generator; templates are pure inspiration."""
    items = await TemplateProgramService(db).list_templates()
    result: list[WorkoutTemplateRead] = []
    for template in items:
        days = []
        for day in template.days:
            exercises = []
            for item in day.exercises:
                exercises.append(
                    {
                        "id": item.id,
                        "created_at": item.created_at,
                        "updated_at": item.updated_at,
                        "position": item.position,
                        "sets": item.sets,
                        "reps_min": item.reps_min,
                        "reps_max": item.reps_max,
                        "rest_sec": item.rest_sec,
                        "target_percent_1rm": item.target_percent_1rm,
                        "notes": item.notes,
                        "exercise_id": item.exercise_id,
                        "exercise_name": item.exercise.name_ru if item.exercise else "",
                        "exercise_slug": item.exercise.slug if item.exercise else "",
                        "muscle": item.exercise.primary_muscle.value if item.exercise else "",
                    },
                )
            days.append(
                {
                    "id": day.id,
                    "created_at": day.created_at,
                    "updated_at": day.updated_at,
                    "day_index": day.day_index,
                    "title": day.title,
                    "focus": day.focus,
                    "is_rest": day.is_rest,
                    "exercises": exercises,
                },
            )
        result.append(
            WorkoutTemplateRead.model_validate(
                {
                    "id": template.id,
                    "slug": template.slug,
                    "name": template.name,
                    "level": template.level,
                    "split_type": template.split_type,
                    "days_per_week": template.days_per_week,
                    "description": template.description,
                    "is_active": template.is_active,
                    "days": days,
                    "created_at": template.created_at,
                    "updated_at": template.updated_at,
                },
            ),
        )
    return result
