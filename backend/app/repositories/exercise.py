from __future__ import annotations

from sqlalchemy import select

from app.models.exercise import Equipment, Exercise, MuscleGroup
from app.repositories.base import BaseRepository


class ExerciseRepository(BaseRepository[Exercise]):
    model = Exercise

    async def get_by_slug(self, slug: str) -> Exercise | None:
        res = await self.db.execute(select(Exercise).where(Exercise.slug == slug))
        return res.scalar_one_or_none()

    async def list_filtered(
        self,
        muscle: MuscleGroup | None = None,
        equipment: list[Equipment] | None = None,
        active_only: bool = True,
    ) -> list[Exercise]:
        stmt = select(Exercise)
        if active_only:
            stmt = stmt.where(Exercise.is_active.is_(True))
        if muscle:
            stmt = stmt.where(Exercise.primary_muscle == muscle)
        if equipment:
            stmt = stmt.where(Exercise.equipment.in_(equipment))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
