from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class AtomicService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def run(self, action: Callable[[], Awaitable[T]]) -> T:
        try:
            result = await action()
            await self.db.commit()
            return result
        except Exception:
            await self.db.rollback()
            raise
