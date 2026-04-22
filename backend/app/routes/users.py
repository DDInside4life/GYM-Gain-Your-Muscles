from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, DbSession
from app.repositories.progress import WeightEntryRepository
from app.repositories.user import UserRepository
from app.schemas.user import UserProfileUpdate, UserRead, WeightEntryCreate, WeightEntryRead

router = APIRouter()


@router.put("/me", response_model=UserRead)
async def update_profile(data: UserProfileUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    repo = UserRepository(db)
    await repo.update(user, **data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.get("/me/weights", response_model=list[WeightEntryRead])
async def list_weights(user: CurrentUser, db: DbSession) -> list[WeightEntryRead]:
    entries = await WeightEntryRepository(db).for_user(user.id)
    return [WeightEntryRead.model_validate(e) for e in entries]


@router.post("/me/weights", response_model=WeightEntryRead, status_code=status.HTTP_201_CREATED)
async def add_weight(data: WeightEntryCreate, user: CurrentUser, db: DbSession) -> WeightEntryRead:
    repo = WeightEntryRepository(db)
    entry = await repo.create(user_id=user.id, weight_kg=data.weight_kg, recorded_at=data.recorded_at)
    await db.commit()
    await db.refresh(entry)
    return WeightEntryRead.model_validate(entry)
