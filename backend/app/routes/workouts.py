"""HTTP layer for workout plans.

Single materialization path: every generation request flows through
:class:`WorkoutGenerator` which produces a multi-week plan with a test week,
RIR/RPE-aware prescriptions and periodization-driven week modifiers. Template
records are surfaced read-only via ``GET /predefined`` for inspiration; they
never bypass the generator.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.models.questionnaire import WorkoutQuestionnaire
from app.models.user import Experience, Goal, Sex
from app.models.workout import SetLog, WorkoutDay, WorkoutExercise
from app.repositories.exercise import ExerciseRepository
from app.repositories.idempotency import IdempotencyRepository
from app.repositories.questionnaire import WorkoutQuestionnaireRepository
from app.repositories.workout import (
    MesocycleRepository,
    SetLogRepository,
    WorkoutPlanRepository,
    WorkoutResultRepository,
)
from app.schemas.questionnaire import WorkoutQuestionnaireInput
from app.schemas.template import WorkoutExerciseWeightInput
from app.schemas.workout import (
    FinalizeTestWeekRead,
    SetLogInput,
    SetLogRead,
    WeekProgressRead,
    WorkoutDayPatch,
    WorkoutExerciseRead,
    WorkoutFeedbackInput,
    WorkoutFeedbackRead,
    WorkoutGenerateInput,
    WorkoutPlanRead,
    WorkoutResultInput,
    WorkoutResultRead,
)
from app.services.workout import ProgressionService, TemplateProgramService, WorkoutGenerator
from app.services.workout.auto_weights import AutoWeightCalculator, adjusted_e1rm
from app.services.atomic import AtomicService
from app.services.idempotency import IdempotencyService

router = APIRouter()


def _questionnaire_input_from_row(row: WorkoutQuestionnaire) -> WorkoutQuestionnaireInput:
    return WorkoutQuestionnaireInput(
        sex=Sex(row.sex),
        age=row.age,
        height_cm=row.height_cm,
        weight_kg=row.weight_kg,
        experience=Experience(row.experience),
        goal=Goal(row.goal),
        location=row.location,
        equipment=list(row.equipment or []),
        injuries=list(row.injuries or []),
        days_per_week=row.days_per_week,
        available_days=list(row.available_days or []),
        notes=row.notes or "",
        session_duration_min=row.session_duration_min,
        training_structure=row.training_structure,
        periodization=row.periodization,
        cycle_length_weeks=row.cycle_length_weeks,
        priority_exercise_ids=list(row.priority_exercise_ids or []),
    )


async def _generate_from_latest_questionnaire(user, db, *, autocommit: bool = True) -> WorkoutPlanRead:
    questionnaire = await WorkoutQuestionnaireRepository(db).latest_for_user(user.id)
    if questionnaire is None:
        raise NotFound("Заполните анкету тренировки перед перегенерацией")
    payload = _questionnaire_input_from_row(questionnaire)
    plan = await WorkoutGenerator(db).generate(
        user, payload, questionnaire_id=questionnaire.id, autocommit=False,
    )
    questionnaire.plan_id = plan.id
    if autocommit:
        await db.commit()
    plan = await WorkoutPlanRepository(db).get_with_days(plan.id) or plan
    return WorkoutPlanRead.model_validate(plan)


@router.post("/generate", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    payload: WorkoutGenerateInput, user: CurrentUser, db: DbSession,
) -> WorkoutPlanRead:
    """Generate a multi-week plan from the legacy short-form payload."""
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
    """Inline generation from a full questionnaire payload (no persistence of the form)."""
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


@router.delete("/history", status_code=status.HTTP_200_OK)
async def clear_history(user: CurrentUser, db: DbSession) -> dict[str, int]:
    deleted = await WorkoutPlanRepository(db).clear_history(user.id)
    await db.commit()
    return {"deleted": deleted}


@router.get("/predefined", response_model=list[dict])
async def predefined_programs(db: DbSession) -> list[dict]:
    """Read-only catalog of seeded templates kept as inspiration only."""
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


@router.post("/progress", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def progress(user: CurrentUser, db: DbSession) -> WorkoutPlanRead:
    """Materialize the next mesocycle from the latest questionnaire."""
    return await _generate_from_latest_questionnaire(user, db)


@router.post("/regenerate", response_model=WorkoutPlanRead, status_code=status.HTTP_201_CREATED)
async def regenerate_next_month(
    user: CurrentUser,
    db: DbSession,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> WorkoutPlanRead:
    async def _action() -> tuple[int, dict]:
        plan = await _generate_from_latest_questionnaire(user, db, autocommit=False)
        return status.HTTP_201_CREATED, plan.model_dump(mode="json")

    idempotency = IdempotencyService(IdempotencyRepository(db))
    result = await AtomicService(db).run(
        lambda: idempotency.execute(
            user_id=user.id,
            operation="workouts.regenerate",
            idempotency_key=idempotency_key,
            request_payload={"user_id": user.id},
            action=_action,
        ),
    )
    response.status_code = result.status_code
    return WorkoutPlanRead.model_validate(result.body)


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


@router.post(
    "/{plan_id}/finalize-test-week",
    response_model=FinalizeTestWeekRead,
    status_code=status.HTTP_200_OK,
)
async def finalize_test_week(
    plan_id: int,
    user: CurrentUser,
    db: DbSession,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> FinalizeTestWeekRead:
    """Compute working weights for weeks 2..N from test-week SetLog data.

    Requires at least one logged set per test-suitable exercise in week 1.
    Rewrites weight_kg / target_percent_1rm / target_rir / rpe_text in-place
    and persists an e1RM snapshot in Mesocycle.weekly_volume.
    """
    plan = await WorkoutPlanRepository(db).get_with_days(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")

    params = plan.params or {}
    try:
        goal = Goal(str(params.get("goal", "general")))
    except ValueError:
        goal = Goal.general
    try:
        experience = Experience(str(params.get("experience", "intermediate")))
    except ValueError:
        experience = Experience.intermediate

    async def _action() -> tuple[int, dict]:
        calc = AutoWeightCalculator(db)
        results = await calc.recalculate_working_weeks(plan, goal, experience)
        e1rm_snapshot = {r.exercise_id: r.e1rm for r in results}

        meso_repo = MesocycleRepository(db)
        meso = await meso_repo.for_plan(plan_id)
        if meso is not None:
            audit = dict(meso.weekly_volume or {})
            audit["e1rm_after_test"] = {str(k): v for k, v in e1rm_snapshot.items()}
            audit["finalized"] = True
            meso.weekly_volume = audit
        payload = {
            "plan_id": plan_id,
            "updated_exercises": len(results),
            "e1rm_snapshot": e1rm_snapshot,
        }
        return status.HTTP_200_OK, payload

    idempotency = IdempotencyService(IdempotencyRepository(db))
    result = await AtomicService(db).run(
        lambda: idempotency.execute(
            user_id=user.id,
            operation="workouts.finalize_test_week",
            idempotency_key=idempotency_key,
            request_payload={"plan_id": plan_id},
            action=_action,
        ),
    )
    response.status_code = result.status_code
    return FinalizeTestWeekRead.model_validate(result.body)


@router.get("/{plan_id}/progress", response_model=list[WeekProgressRead])
async def plan_progress(plan_id: int, user: CurrentUser, db: DbSession) -> list[WeekProgressRead]:
    """Weekly summary: completed vs planned sets, top e1RM per exercise."""
    plan = await WorkoutPlanRepository(db).get_with_days(plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")

    set_log_repo = SetLogRepository(db)
    top_e1rm = await set_log_repo.top_e1rm_for_plan(plan_id)

    weeks_map: dict[int, dict] = {}
    for day in plan.days:
        if day.is_rest:
            continue
        wi = day.week_index
        if wi not in weeks_map:
            weeks_map[wi] = {"planned_sets": 0, "completed_sets": 0}
        for ex in day.exercises:
            weeks_map[wi]["planned_sets"] += ex.sets

    all_logs_stmt = select(SetLog).where(SetLog.plan_id == plan_id)
    all_logs = (await db.execute(all_logs_stmt)).scalars().all()
    for log in all_logs:
        wi = log.week_index
        if wi not in weeks_map:
            weeks_map[wi] = {"planned_sets": 0, "completed_sets": 0}
        weeks_map[wi]["completed_sets"] = weeks_map[wi].get("completed_sets", 0) + 1

    result: list[WeekProgressRead] = []
    for wi in sorted(weeks_map):
        planned = weeks_map[wi]["planned_sets"]
        completed = weeks_map[wi]["completed_sets"]
        week_e1rm = {ex_id: e1rm for ex_id, e1rm in top_e1rm.items()}
        if completed >= planned and planned > 0:
            week_status: str = "complete"
        elif completed > 0:
            week_status = "in_progress"
        else:
            week_status = "upcoming"
        result.append(WeekProgressRead(
            week_index=wi,
            completed_sets=completed,
            planned_sets=planned,
            top_e1rm_per_exercise=week_e1rm,
            week_status=week_status,
        ))
    return result


@router.post("/sets", response_model=SetLogRead, status_code=status.HTTP_201_CREATED)
async def log_set(
    payload: SetLogInput,
    user: CurrentUser,
    db: DbSession,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> SetLogRead:
    """Log a completed set. Backend computes volume and adjusted e1RM."""
    we = await db.get(WorkoutExercise, payload.workout_exercise_id)
    if we is None:
        raise NotFound("Упражнение тренировки не найдено")
    day = await db.get(WorkoutDay, we.day_id)
    if day is None:
        raise NotFound("День тренировки не найден")
    plan = await WorkoutPlanRepository(db).get(day.plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")

    async def _action() -> tuple[int, dict]:
        volume = round(payload.completed_weight_kg * payload.completed_reps, 2)
        e1rm = adjusted_e1rm(payload.completed_weight_kg, payload.completed_reps, payload.rir)
        log = SetLog(
            user_id=user.id,
            plan_id=plan.id,
            day_id=day.id,
            workout_exercise_id=we.id,
            exercise_id=we.exercise_id,
            week_index=day.week_index,
            set_index=payload.set_index,
            planned_weight_kg=we.weight_kg,
            completed_reps=payload.completed_reps,
            completed_weight_kg=payload.completed_weight_kg,
            rir=payload.rir,
            volume=volume,
            estimated_1rm=e1rm,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)

        meso_repo = MesocycleRepository(db)
        meso = await meso_repo.for_plan(plan.id)
        if meso is not None and meso.current_week != day.week_index:
            meso.current_week = day.week_index
        return status.HTTP_201_CREATED, SetLogRead.model_validate(log).model_dump(mode="json")

    idempotency = IdempotencyService(IdempotencyRepository(db))
    result = await AtomicService(db).run(
        lambda: idempotency.execute(
            user_id=user.id,
            operation="workouts.log_set",
            idempotency_key=idempotency_key,
            request_payload=payload.model_dump(),
            action=_action,
        ),
    )
    response.status_code = result.status_code
    return SetLogRead.model_validate(result.body)


@router.delete("/sets/{log_id}", status_code=status.HTTP_200_OK)
async def delete_set_log(log_id: int, user: CurrentUser, db: DbSession) -> None:
    """Remove an erroneously logged set."""
    log = await db.get(SetLog, log_id)
    if log is None or log.user_id != user.id:
        raise NotFound("Запись не найдена")
    await db.delete(log)
    await db.commit()


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
            superset_group=item.superset_group,
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


@router.patch(
    "/exercises/{workout_exercise_id}/weight",
    response_model=WorkoutExerciseRead,
)
async def update_exercise_weight(
    workout_exercise_id: int,
    payload: WorkoutExerciseWeightInput,
    user: CurrentUser,
    db: DbSession,
) -> WorkoutExerciseRead:
    we = await db.get(WorkoutExercise, workout_exercise_id)
    if we is None:
        raise NotFound("Упражнение не найдено")
    day = await db.get(WorkoutDay, we.day_id)
    if day is None:
        raise NotFound("День тренировки не найден")
    plan = await WorkoutPlanRepository(db).get(day.plan_id)
    if plan is None or plan.user_id != user.id:
        raise NotFound("План не найден")
    we.weight_kg = payload.weight_kg
    await db.commit()
    stmt = (
        select(WorkoutExercise)
        .where(WorkoutExercise.id == workout_exercise_id)
        .options(selectinload(WorkoutExercise.exercise))
    )
    fresh = (await db.execute(stmt)).scalar_one()
    return WorkoutExerciseRead.model_validate(fresh)


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
