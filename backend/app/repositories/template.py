from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.models.workout_template import TemplateDay, TemplateExercise, WorkoutTemplate
from app.repositories.base import BaseRepository


def _template_eager():
    return (
        selectinload(WorkoutTemplate.days)
        .selectinload(TemplateDay.exercises)
        .joinedload(TemplateExercise.exercise)
    )


class WorkoutTemplateRepository(BaseRepository[WorkoutTemplate]):
    model = WorkoutTemplate

    async def list_active(self) -> list[WorkoutTemplate]:
        stmt = (
            select(WorkoutTemplate)
            .where(WorkoutTemplate.is_active.is_(True))
            .order_by(WorkoutTemplate.days_per_week.asc(), WorkoutTemplate.id.asc())
            .options(_template_eager())
        )
        res = await self.db.execute(stmt)
        return list(res.unique().scalars().all())

    async def get_with_days(self, template_id: int) -> WorkoutTemplate | None:
        stmt = (
            select(WorkoutTemplate)
            .where(WorkoutTemplate.id == template_id, WorkoutTemplate.is_active.is_(True))
            .options(_template_eager())
        )
        res = await self.db.execute(stmt)
        return res.unique().scalars().first()
