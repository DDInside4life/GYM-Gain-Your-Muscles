from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.core.deps import CurrentAdmin, DbSession
from app.core.exceptions import Conflict, NotFound
from app.models.exercise import Equipment, MuscleGroup
from app.repositories.exercise import ExerciseRepository
from app.schemas.exercise import ExerciseCreate, ExerciseRead, ExerciseUpdate

router = APIRouter()


@router.get("", response_model=list[ExerciseRead])
async def list_exercises(
    db: DbSession,
    muscle: MuscleGroup | None = Query(default=None),
    equipment: list[Equipment] | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1, max_length=120),
) -> list[ExerciseRead]:
    exercises = await ExerciseRepository(db).list_filtered(muscle=muscle, equipment=equipment, query=q)
    return [ExerciseRead.model_validate(e) for e in exercises]


@router.get("/{exercise_id:int}", response_model=ExerciseRead)
async def get_exercise_by_id(exercise_id: int, db: DbSession) -> ExerciseRead:
    ex = await ExerciseRepository(db).get(exercise_id)
    if not ex:
        raise NotFound("Exercise not found")
    return ExerciseRead.model_validate(ex)


@router.get("/slug/{slug}", response_model=ExerciseRead)
@router.get("/{slug}", response_model=ExerciseRead, include_in_schema=False)
async def get_exercise(slug: str, db: DbSession) -> ExerciseRead:
    ex = await ExerciseRepository(db).get_by_slug(slug)
    if not ex:
        raise NotFound("Exercise not found")
    return ExerciseRead.model_validate(ex)


@router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
async def create_exercise(data: ExerciseCreate, _: CurrentAdmin, db: DbSession) -> ExerciseRead:
    repo = ExerciseRepository(db)
    if await repo.get_by_slug(data.slug):
        raise Conflict("Slug exists")
    ex = await repo.create(**data.model_dump())
    await db.commit()
    await db.refresh(ex)
    return ExerciseRead.model_validate(ex)


@router.put("/{slug}", response_model=ExerciseRead)
async def update_exercise(slug: str, data: ExerciseUpdate, _: CurrentAdmin, db: DbSession) -> ExerciseRead:
    repo = ExerciseRepository(db)
    ex = await repo.get_by_slug(slug)
    if not ex:
        raise NotFound("Exercise not found")
    await repo.update(ex, **data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(ex)
    return ExerciseRead.model_validate(ex)


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_exercise(slug: str, _: CurrentAdmin, db: DbSession) -> Response:
    repo = ExerciseRepository(db)
    ex = await repo.get_by_slug(slug)
    if not ex:
        raise NotFound("Exercise not found")
    await repo.delete(ex)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
