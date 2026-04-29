from __future__ import annotations

from sqlalchemy import select

from app.models.idempotency import IdempotencyRecord
from app.repositories.base import BaseRepository


class IdempotencyRepository(BaseRepository[IdempotencyRecord]):
    model = IdempotencyRecord

    async def get_by_scope(
        self,
        *,
        user_id: int,
        operation: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        stmt = (
            select(IdempotencyRecord)
            .where(
                IdempotencyRecord.user_id == user_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
