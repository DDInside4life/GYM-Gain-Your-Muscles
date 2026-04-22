from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.blog import BlogPost
from app.models.exercise import Exercise
from app.models.forum import ForumQuestion
from app.models.user import User
from app.models.workout import WorkoutPlan


class AdminService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analytics(self) -> dict:
        async def n(model) -> int:
            res = await self.db.execute(select(func.count()).select_from(model))
            return int(res.scalar_one())

        return {
            "users": await n(User),
            "exercises": await n(Exercise),
            "workout_plans": await n(WorkoutPlan),
            "blog_posts": await n(BlogPost),
            "forum_questions": await n(ForumQuestion),
        }
