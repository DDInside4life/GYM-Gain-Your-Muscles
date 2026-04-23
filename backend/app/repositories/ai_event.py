from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select

from app.models.ai_event import AIEvent
from app.repositories.base import BaseRepository


class AIEventRepository(BaseRepository[AIEvent]):
    model = AIEvent

    async def log(
        self,
        *,
        user_id: int,
        kind: str,
        source: str,
        model: str | None = None,
        plan_id: int | None = None,
        nutrition_plan_id: int | None = None,
        prompt: str | None = None,
        response: str | None = None,
        output: dict[str, Any] | None = None,
        explanation: dict[str, Any] | None = None,
        latency_ms: int = 0,
        error: str | None = None,
    ) -> AIEvent:
        row = AIEvent(
            user_id=user_id, kind=kind, source=source, model=model,
            plan_id=plan_id, nutrition_plan_id=nutrition_plan_id,
            prompt=(prompt or "")[:20000] or None,
            response=(response or "")[:20000] or None,
            output=output or {}, explanation=explanation or {},
            latency_ms=latency_ms, error=error,
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def latest_for_plan(self, plan_id: int) -> AIEvent | None:
        stmt = (
            select(AIEvent)
            .where(AIEvent.plan_id == plan_id)
            .order_by(desc(AIEvent.id))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def latest_for_user(self, user_id: int, kind: str, limit: int = 10) -> list[AIEvent]:
        stmt = (
            select(AIEvent)
            .where(AIEvent.user_id == user_id, AIEvent.kind == kind)
            .order_by(desc(AIEvent.id))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
