from __future__ import annotations

from sqlalchemy import desc, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import joinedload, selectinload

from app.models.workout import Difficulty, WorkoutDay, WorkoutExercise, WorkoutFeedback, WorkoutPlan
from app.repositories.base import BaseRepository


def _plan_eager():
    return (
        selectinload(WorkoutPlan.days)
        .selectinload(WorkoutDay.exercises)
        .joinedload(WorkoutExercise.exercise)
    )


class WorkoutPlanRepository(BaseRepository[WorkoutPlan]):
    model = WorkoutPlan

    async def latest_for_user(self, user_id: int) -> WorkoutPlan | None:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(desc(WorkoutPlan.week_number), desc(WorkoutPlan.id))
            .options(_plan_eager())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.unique().scalars().first()

    async def get_with_days(self, plan_id: int) -> WorkoutPlan | None:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.id == plan_id)
            .options(_plan_eager())
        )
        res = await self.db.execute(stmt)
        return res.unique().scalars().first()

    async def history(self, user_id: int, limit: int = 20) -> list[WorkoutPlan]:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id)
            .order_by(desc(WorkoutPlan.week_number), desc(WorkoutPlan.id))
            .options(_plan_eager())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.unique().scalars().all())

    async def deactivate_all(self, user_id: int) -> None:
        await self.db.execute(
            update(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_active.is_(True))
            .values(is_active=False)
        )


class WorkoutFeedbackRepository(BaseRepository[WorkoutFeedback]):
    model = WorkoutFeedback

    async def latest_per_day_for_plan(self, plan_id: int, user_id: int) -> list[WorkoutFeedback]:
        stmt = (
            select(WorkoutFeedback)
            .join(WorkoutDay, WorkoutDay.id == WorkoutFeedback.day_id)
            .where(WorkoutDay.plan_id == plan_id, WorkoutFeedback.user_id == user_id)
            .order_by(WorkoutFeedback.day_id, desc(WorkoutFeedback.updated_at))
        )
        res = await self.db.execute(stmt)
        rows = list(res.scalars().all())
        seen: set[int] = set()
        latest: list[WorkoutFeedback] = []
        for fb in rows:
            if fb.day_id in seen:
                continue
            seen.add(fb.day_id)
            latest.append(fb)
        return latest

    async def upsert(
        self,
        *,
        day_id: int,
        user_id: int,
        completed: bool,
        difficulty: Difficulty,
        discomfort: list[str],
        note: str,
    ) -> WorkoutFeedback:
        stmt = (
            pg_insert(WorkoutFeedback)
            .values(
                day_id=day_id, user_id=user_id, completed=completed,
                difficulty=difficulty, discomfort=discomfort, note=note,
            )
            .on_conflict_do_update(
                constraint="uq_workout_feedback_day_user",
                set_={
                    "completed": completed,
                    "difficulty": difficulty,
                    "discomfort": discomfort,
                    "note": note,
                },
            )
            .returning(WorkoutFeedback)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()
