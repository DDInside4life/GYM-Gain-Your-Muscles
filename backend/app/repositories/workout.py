from __future__ import annotations

from sqlalchemy import delete, desc, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import joinedload, selectinload

from app.models.workout import (
    Difficulty, Mesocycle, SetLog, WorkoutDay, WorkoutExercise, WorkoutFeedback, WorkoutPlan, WorkoutResult,
)
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

    async def by_user_and_month(self, user_id: int, month_index: int) -> WorkoutPlan | None:
        stmt = (
            select(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.month_index == month_index)
            .order_by(desc(WorkoutPlan.id))
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

    async def mark_active(self, user_id: int, plan_id: int) -> WorkoutPlan | None:
        await self.deactivate_all(user_id)
        await self.db.execute(
            update(WorkoutPlan)
            .where(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == user_id)
            .values(is_active=True)
        )
        await self.db.flush()
        return await self.get_with_days(plan_id)

    async def deactivate_all(self, user_id: int) -> None:
        await self.db.execute(
            update(WorkoutPlan)
            .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_active.is_(True))
            .values(is_active=False)
        )

    async def clear_history(self, user_id: int) -> int:
        stmt = delete(WorkoutPlan).where(
            WorkoutPlan.user_id == user_id,
            WorkoutPlan.is_active.is_(False),
        )
        result = await self.db.execute(stmt)
        return int(result.rowcount or 0)


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


class WorkoutResultRepository(BaseRepository[WorkoutResult]):
    model = WorkoutResult

    async def by_exercise_latest(self, user_id: int, exercise_id: int) -> WorkoutResult | None:
        stmt = (
            select(WorkoutResult)
            .where(WorkoutResult.user_id == user_id, WorkoutResult.exercise_id == exercise_id)
            .order_by(desc(WorkoutResult.created_at))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: int,
        plan_id: int,
        day_id: int,
        workout_exercise_id: int,
        exercise_id: int,
        week_index: int,
        reps_completed: int,
        weight_kg: float,
        estimated_1rm: float,
    ) -> WorkoutResult:
        stmt = (
            pg_insert(WorkoutResult)
            .values(
                user_id=user_id,
                plan_id=plan_id,
                day_id=day_id,
                workout_exercise_id=workout_exercise_id,
                exercise_id=exercise_id,
                week_index=week_index,
                reps_completed=reps_completed,
                weight_kg=weight_kg,
                estimated_1rm=estimated_1rm,
            )
            .on_conflict_do_update(
                constraint="uq_workout_result_exercise_user",
                set_={
                    "reps_completed": reps_completed,
                    "weight_kg": weight_kg,
                    "estimated_1rm": estimated_1rm,
                    "week_index": week_index,
                },
            )
            .returning(WorkoutResult)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one()


class MesocycleRepository(BaseRepository[Mesocycle]):
    model = Mesocycle

    async def active_for_user(self, user_id: int) -> Mesocycle | None:
        stmt = (
            select(Mesocycle)
            .where(Mesocycle.user_id == user_id, Mesocycle.is_active.is_(True))
            .order_by(desc(Mesocycle.id))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def for_plan(self, plan_id: int) -> Mesocycle | None:
        stmt = (
            select(Mesocycle)
            .where(Mesocycle.plan_id == plan_id)
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def deactivate_user_cycles(self, user_id: int) -> None:
        await self.db.execute(
            update(Mesocycle)
            .where(Mesocycle.user_id == user_id, Mesocycle.is_active.is_(True))
            .values(is_active=False)
        )


class SetLogRepository(BaseRepository[SetLog]):
    model = SetLog

    async def weekly_volume(self, user_id: int, plan_id: int) -> dict[int, float]:
        stmt = (
            select(SetLog.week_index, SetLog.volume)
            .where(SetLog.user_id == user_id, SetLog.plan_id == plan_id)
            .order_by(SetLog.week_index.asc())
        )
        res = await self.db.execute(stmt)
        totals: dict[int, float] = {}
        for week_index, volume in res.all():
            totals[week_index] = totals.get(week_index, 0.0) + float(volume)
        return totals

    async def strength_timeline(self, user_id: int, limit: int = 120) -> list[SetLog]:
        stmt = (
            select(SetLog)
            .where(SetLog.user_id == user_id)
            .order_by(desc(SetLog.created_at))
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(reversed(res.scalars().all()))

    async def for_plan_day(self, plan_id: int, day_id: int) -> list[SetLog]:
        stmt = (
            select(SetLog)
            .where(SetLog.plan_id == plan_id, SetLog.day_id == day_id)
            .order_by(SetLog.workout_exercise_id, SetLog.set_index)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def for_plan_week(self, plan_id: int, week_index: int) -> list[SetLog]:
        stmt = (
            select(SetLog)
            .where(SetLog.plan_id == plan_id, SetLog.week_index == week_index)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def top_e1rm_for_plan(self, plan_id: int) -> dict[int, float]:
        stmt = (
            select(SetLog.exercise_id, SetLog.estimated_1rm)
            .where(SetLog.plan_id == plan_id)
        )
        res = await self.db.execute(stmt)
        best: dict[int, float] = {}
        for exercise_id, e1rm in res.all():
            if e1rm > best.get(exercise_id, 0.0):
                best[exercise_id] = float(e1rm)
        return best
