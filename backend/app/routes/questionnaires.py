from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.models.questionnaire import WorkoutQuestionnaire
from app.repositories.questionnaire import WorkoutQuestionnaireRepository
from app.repositories.workout import WorkoutPlanRepository
from app.schemas.questionnaire import WorkoutQuestionnaireInput, WorkoutQuestionnaireRead
from app.schemas.workout import WorkoutPlanRead
from app.services.workout import WorkoutGenerator

router = APIRouter()


def _to_orm(user_id: int, payload: WorkoutQuestionnaireInput) -> WorkoutQuestionnaire:
    return WorkoutQuestionnaire(
        user_id=user_id,
        sex=payload.sex.value,
        age=payload.age,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        experience=payload.experience.value,
        goal=payload.goal.value,
        location=payload.location,
        equipment=list(payload.equipment),
        injuries=list(payload.injuries),
        days_per_week=payload.days_per_week,
        available_days=list(payload.available_days),
        notes=payload.notes,
        config={
            "version": 1,
        },
    )


@router.post("", response_model=WorkoutQuestionnaireRead, status_code=status.HTTP_201_CREATED)
async def create_questionnaire(
    payload: WorkoutQuestionnaireInput,
    user: CurrentUser,
    db: DbSession,
) -> WorkoutQuestionnaireRead:
    repo = WorkoutQuestionnaireRepository(db)
    row = await repo.add(_to_orm(user.id, payload))
    await db.commit()
    await db.refresh(row)
    return WorkoutQuestionnaireRead.model_validate(row)


@router.get("/latest", response_model=WorkoutQuestionnaireRead | None)
async def latest_questionnaire(user: CurrentUser, db: DbSession) -> WorkoutQuestionnaireRead | None:
    row = await WorkoutQuestionnaireRepository(db).latest_for_user(user.id)
    return WorkoutQuestionnaireRead.model_validate(row) if row else None


@router.get("", response_model=list[WorkoutQuestionnaireRead])
async def list_questionnaires(user: CurrentUser, db: DbSession) -> list[WorkoutQuestionnaireRead]:
    rows = await WorkoutQuestionnaireRepository(db).history(user.id)
    return [WorkoutQuestionnaireRead.model_validate(r) for r in rows]


@router.post(
    "/{questionnaire_id}/generate",
    response_model=WorkoutPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_from_questionnaire(
    questionnaire_id: int,
    user: CurrentUser,
    db: DbSession,
) -> WorkoutPlanRead:
    repo = WorkoutQuestionnaireRepository(db)
    row = await repo.get(questionnaire_id)
    if row is None or row.user_id != user.id:
        raise NotFound("Анкета не найдена")
    payload = WorkoutQuestionnaireInput.model_validate({
        "sex": row.sex, "age": row.age, "height_cm": row.height_cm, "weight_kg": row.weight_kg,
        "experience": row.experience, "goal": row.goal, "location": row.location,
        "equipment": row.equipment, "injuries": row.injuries,
        "days_per_week": row.days_per_week, "available_days": row.available_days,
        "notes": row.notes,
    })
    plan = await WorkoutGenerator(db).generate(user, payload, questionnaire_id=row.id)
    row.plan_id = plan.id
    await db.commit()
    plan = await WorkoutPlanRepository(db).get_with_days(plan.id) or plan
    return WorkoutPlanRead.model_validate(plan)
