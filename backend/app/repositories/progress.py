from __future__ import annotations

from sqlalchemy import asc, select

from app.models.progress import WeightEntry
from app.repositories.base import BaseRepository


class WeightEntryRepository(BaseRepository[WeightEntry]):
    model = WeightEntry

    async def for_user(self, user_id: int) -> list[WeightEntry]:
        stmt = (
            select(WeightEntry)
            .where(WeightEntry.user_id == user_id)
            .order_by(asc(WeightEntry.recorded_at))
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
