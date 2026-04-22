from __future__ import annotations

from sqlalchemy import and_, desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from app.models.forum import ForumComment, ForumQuestion, ForumReaction
from app.repositories.base import BaseRepository


class ForumQuestionRepository(BaseRepository[ForumQuestion]):
    model = ForumQuestion

    async def list_approved(self, limit: int = 30, offset: int = 0) -> list[ForumQuestion]:
        stmt = (
            select(ForumQuestion)
            .where(ForumQuestion.is_approved.is_(True))
            .order_by(desc(ForumQuestion.created_at))
            .limit(limit).offset(offset)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_with_comments(self, question_id: int) -> ForumQuestion | None:
        stmt = (
            select(ForumQuestion)
            .where(ForumQuestion.id == question_id)
            .options(selectinload(ForumQuestion.comments))
        )
        res = await self.db.execute(stmt)
        return res.scalars().first()


class ForumCommentRepository(BaseRepository[ForumComment]):
    model = ForumComment


class ForumReactionRepository(BaseRepository[ForumReaction]):
    model = ForumReaction

    async def toggle(
        self, *, user_id: int, target_type: str, target_id: int, reaction: str,
    ) -> bool:
        """Returns True if reaction was added, False if removed."""
        existing = await self.db.execute(
            select(ForumReaction).where(and_(
                ForumReaction.user_id == user_id,
                ForumReaction.target_type == target_type,
                ForumReaction.target_id == target_id,
                ForumReaction.reaction == reaction,
            ))
        )
        row = existing.scalar_one_or_none()
        if row is not None:
            await self.db.delete(row)
            await self.db.flush()
            return False
        stmt = pg_insert(ForumReaction).values(
            user_id=user_id, target_type=target_type, target_id=target_id, reaction=reaction,
        ).on_conflict_do_nothing(constraint="uq_forum_reactions")
        await self.db.execute(stmt)
        await self.db.flush()
        return True

    async def counts(self, target_type: str, target_ids: list[int]) -> dict[int, dict[str, int]]:
        if not target_ids:
            return {}
        stmt = (
            select(ForumReaction.target_id, ForumReaction.reaction, func.count().label("n"))
            .where(ForumReaction.target_type == target_type, ForumReaction.target_id.in_(target_ids))
            .group_by(ForumReaction.target_id, ForumReaction.reaction)
        )
        res = await self.db.execute(stmt)
        out: dict[int, dict[str, int]] = {tid: {} for tid in target_ids}
        for tid, reaction, n in res.all():
            out[tid][reaction] = int(n)
        return out
