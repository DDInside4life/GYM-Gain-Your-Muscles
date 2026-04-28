from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.models.workout import WorkoutDay, WorkoutExercise
from app.repositories.exercise import ExerciseRepository
from app.repositories.questionnaire import WorkoutQuestionnaireRepository
from app.repositories.workout import WorkoutPlanRepository, WorkoutResultRepository
from app.schemas.questionnaire import WorkoutQuestionnaireInput
from app.schemas.template import TemplateGenerateWorkoutInput
from app.schemas.workout import (
    WorkoutDayPatch, WorkoutFeedbackInput, WorkoutFeedbackRead, WorkoutGenerateInput, WorkoutPlanRead,
    WorkoutResultInput, WorkoutResultRead,
)
from app.services.workout import ProgressionService, TemplateProgramService, WorkoutGenerator

router = APIRouter()


@router.post("/generate", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    payload: WorkoutGenerateInput, user: CurrentUser, db: DbSession,
) -> WorkoutPlanRead:
    plan = await WorkoutGenerator(db).generate(user, payload)
    return WorkoutPlanRead.model_validate(plan)


@router.post(
    "/generate-from-questionnaire",
    response_model=WorkoutPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_from_questionnaire_inline(
    payload: WorkoutQuestionnaireInput, user: CurrentUser, db: DbSession,
) -> WorkoutPlanRead:
    plan = await WorkoutGenerator(db).generate(user, payload)
    return WorkoutPlanRead.model_validate(plan)


@router.get("/current", response_model=WorkoutPlanRead | None)
async def current_plan(user: CurrentUser, db: DbSession) -> WorkoutPlanRead | None:
    plan = await WorkoutPlanRepository(db).latest_for_user(user.id)
    return WorkoutPlanRead.model_validate(plan) if plan else None


@router.get("/history", response_model=list[WorkoutPlanRead])
async def history(user: CurrentUser, db: DbSession) -> list[WorkoutPlanRead]:
    items = await WorkoutPlanRepository(db).history(user.id)
    return [WorkoutPlanRead.model_validate(p) for p in items]


@router.get("/predefined", response_model=list[dict])
async def predefined_programs(db: DbSession) -> list[dict]:
    templates = await TemplateProgramService(db).list_templates()
    return [
        {
            "id": item.id,
            "slug": item.slug,
            "name": item.name,
            "days_per_week": item.days_per_week,
            "level": item.level,
            "split_type": item.split_type,
            "description": item.description,
        }
        for item in templates
    ]


@router.post(
    "/generate-from-template",
    response_model=WorkoutPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def generate_from_template(
    payload: TemplateGenerateWorkoutInput,
    user: CurrentUser,
    db: DbSession,
) -> WorkoutPlanRead:
    plan, _ = await TemplateProgramService(db).generate_from_template(user, payload)
    return WorkoutPlanRead.model_validate(plan)


@router.post("/progress", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def progress(user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    current = await WorkoutPlanRepository(db).latest_for_user(user.id)
    if current is None:
        raise NotFound("Нет активного плана")
    params = current.params or {}
    payload = WorkoutGenerateInput(
        weight_kg=float(getattr(user, "weight_kg", 75) or 75),
        height_cm=float(getattr(user, "height_cm", 175) or 175),
        age=28,
        experience=params.get("experience", getattr(user, "experience", "intermediate")),
        goal=params.get("goal", getattr(user, "goal", "muscle_gain")),
        equipment=params.get("equipment", ["bodyweight", "dumbbell", "barbell", "machine"]),
        injuries=params.get("injuries", []),
        days_per_week=int(params.get("days_per_week", 4)),
    )
    plan = await WorkoutGenerator(db).generate(user, payload)
    return WorkoutPlanRead.model_validate(plan)


@router.post("/regenerate", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def regenerate_next_month(user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    questionnaire = await WorkoutQuestionnaireRepository(db).latest_for_user(user.id)
    if questionnaire is None:
        raise NotFound("Заполните анкету тренировки перед перегенерацией")
    payload = WorkoutQuestionnaireInput.model_validate({
        "sex": questionnaire.sex,
        "age": questionnaire.age,
        "height_cm": questionnaire.height_cm,
        "weight_kg": questionnaire.weight_kg,
        "experience": questionnaire.experience,
        "goal": questionnaire.goal,
        "location": questionnaire.location,
        "equipment": questionnaire.equipment,
        "injuries": questionnaire.injuries,
        "days_per_week": questionnaire.days_per_week,
        "available_days": questionnaire.available_days,
        "notes": questionnaire.notes,
    })
    plan = await WorkoutGenerator(db).generate(user, payload, questionnaire_id=questionnaire.id)
    questionnaire.plan_id = plan.id
    await db.commit()
    plan = await WorkoutPlanRepository(db).get_with_days(plan.id) or plan
    return WorkoutPlanRead.model_validate(plan)


@router.post("/feedback", response_model=WorkoutFeedbackRead, status_code=status.HTTP_201_CREATED)
async def feedback(
    payload: WorkoutFeedbackInput, user: CurrentUser, db: DbSession,
) -> WorkoutFeedbackRead:
    fb = await ProgressionService(db).submit_feedback(
        user, payload.day_id, payload.completed, payload.difficulty,
        payload.discomfort, payload.note,
    )
    return WorkoutFeedbackRead.model_validate(fb)


@router.get("/{plan_id}", response_model=WorkoutPlanRead)
async def get_plan(plan_id: int, user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    plan = await WorkoutPlanRepository(db).get_with_days(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")
    return WorkoutPlanRead.model_validate(plan)


@router.post("/{plan_id}/select", response_model=WorkoutPlanRead)
async def select_plan(plan_id: int, user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    repo = WorkoutPlanRepository(db)
    plan = await repo.mark_active(user.id, plan_id)
    if plan is None:
        raise NotFound("План не найден")
    await db.commit()
    fresh = await repo.get_with_days(plan_id)
    assert fresh is not None
    return WorkoutPlanRead.model_validate(fresh)


@router.put("/{plan_id}/days/{day_id}", response_model=WorkoutPlanRead)
async def update_day(
    plan_id: int, day_id: int, payload: WorkoutDayPatch, user: CurrentUser, db: DbSession,
) -> WorkoutPlanRead:
    repo = WorkoutPlanRepository(db)
    plan = await repo.get_with_days(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")
    day = next((d for d in plan.days if d.id == day_id), None)
    if day is None:
        raise NotFound("День не найден")

    exercise_ids = {item.exercise_id for item in payload.exercises}
    valid_exercises = {
        ex.id: ex
        for ex in (
            await ExerciseRepository(db).list_filtered(active_only=True)
        )
        if ex.id in exercise_ids
    }
    if exercise_ids and len(valid_exercises) != len(exercise_ids):
        raise NotFound("Одно из упражнений не найдено или неактивно")

    previous_ids = {ex.exercise_id for ex in day.exercises}
    new_ids = exercise_ids
    removed = previous_ids - new_ids
    added = new_ids - previous_ids

    day.exercises.clear()
    for pos, item in enumerate(payload.exercises):
        day.exercises.append(WorkoutExercise(
            day_id=day.id,
            exercise_id=item.exercise_id,
            position=pos,
            sets=item.sets,
            reps_min=item.reps_min,
            reps_max=item.reps_max,
            weight_kg=item.weight_kg,
            rest_sec=item.rest_sec,
            notes=item.notes,
            target_percent_1rm=item.target_percent_1rm,
            is_test_set=item.is_test_set,
            test_instruction=item.test_instruction,
            target_rir=item.target_rir,
            rpe_text=item.rpe_text,
        ))

    history = dict(plan.params or {})
    edits = dict(history.get("user_edits") or {})
    avoid = set(edits.get("avoid_exercise_ids") or []) | removed
    prefer = (set(edits.get("prefer_exercise_ids") or []) | added) - removed
    edits["avoid_exercise_ids"] = sorted(avoid)
    edits["prefer_exercise_ids"] = sorted(prefer)
    history["user_edits"] = edits
    plan.params = history

    await db.commit()
    fresh = await repo.get_with_days(plan_id)
    assert fresh is not None
    return WorkoutPlanRead.model_validate(fresh)


@router.post("/results", response_model=WorkoutResultRead, status_code=status.HTTP_201_CREATED)
async def submit_result(
    payload: WorkoutResultInput, user: CurrentUser, db: DbSession,
) -> WorkoutResultRead:
    we = await db.get(WorkoutExercise, payload.workout_exercise_id)
    if we is None:
        raise NotFound("Упражнение тренировки не найдено")
    day = await db.get(WorkoutDay, we.day_id)
    if day is None:
        raise NotFound("День тренировки не найден")
    plan = await WorkoutPlanRepository(db).get(day.plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")
    exercise = await ExerciseRepository(db).get(we.exercise_id)
    if exercise is None:
        raise NotFound("Упражнение не найдено")
    estimated = round(payload.weight_kg * (1 + payload.reps_completed / 30.0), 2)
    row = await WorkoutResultRepository(db).upsert(
        user_id=user.id,
        plan_id=plan.id,
        day_id=day.id,
        workout_exercise_id=we.id,
        exercise_id=exercise.id,
        week_index=day.week_index,
        reps_completed=payload.reps_completed,
        weight_kg=payload.weight_kg,
        estimated_1rm=estimated,
    )
    await db.commit()
    await db.refresh(row)
    return WorkoutResultRead.model_validate(row)
