from __future__ import annotations

from sqlalchemy import select
from sqlalchemy import or_

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
        query: str | None = None,
        active_only: bool = True,
    ) -> list[Exercise]:
        stmt = select(Exercise)
        if active_only:
            stmt = stmt.where(Exercise.is_active.is_(True))
        if muscle:
            stmt = stmt.where(Exercise.primary_muscle == muscle)
        if equipment:
            stmt = stmt.where(Exercise.equipment.in_(equipment))
        if query:
            q = f"%{query.strip().lower()}%"
            stmt = stmt.where(or_(
                Exercise.name_ru.ilike(q),
                Exercise.name_en.ilike(q),
                Exercise.name.ilike(q),
                Exercise.description.ilike(q),
            ))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
