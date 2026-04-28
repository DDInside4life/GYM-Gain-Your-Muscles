from __future__ import annotations

from sqlalchemy import desc, select

from app.models.questionnaire import WorkoutQuestionnaire
from app.repositories.base import BaseRepository


class WorkoutQuestionnaireRepository(BaseRepository[WorkoutQuestionnaire]):
    model = WorkoutQuestionnaire

    async def latest_for_user(self, user_id: int) -> WorkoutQuestionnaire | None:
        stmt = (
            select(WorkoutQuestionnaire)
            .where(WorkoutQuestionnaire.user_id == user_id)
            .order_by(desc(WorkoutQuestionnaire.created_at))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def history(self, user_id: int, limit: int = 20) -> list[WorkoutQuestionnaire]:
        stmt = (
            select(WorkoutQuestionnaire)
            .where(WorkoutQuestionnaire.user_id == user_id)
            .order_by(desc(WorkoutQuestionnaire.created_at))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
