from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFound
from app.models.forum import ForumComment, ForumQuestion
from app.models.user import User
from app.repositories.forum import (
    ForumCommentRepository, ForumQuestionRepository, ForumReactionRepository,
)
from app.schemas.forum import ForumCommentCreate, ForumQuestionCreate


class ForumService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.questions = ForumQuestionRepository(db)
        self.comments = ForumCommentRepository(db)
        self.reactions = ForumReactionRepository(db)

    async def create_question(self, user: User, data: ForumQuestionCreate) -> ForumQuestion:
        q = await self.questions.create(
            user_id=user.id,
            title=data.title.strip(),
            body=data.body.strip(),
            tags=[t.strip().lower() for t in data.tags if t.strip()][:10],
            is_approved=True,
        )
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def add_comment(
        self, user: User, question_id: int, data: ForumCommentCreate,
    ) -> ForumComment:
        question = await self.questions.get(question_id)
        if question is None:
            raise NotFound("Question not found")
        if data.parent_id is not None:
            parent = await self.comments.get(data.parent_id)
            if parent is None or parent.question_id != question_id:
                raise NotFound("Parent comment not found")
        c = await self.comments.create(
            question_id=question_id,
            parent_id=data.parent_id,
            user_id=user.id,
            body=data.body.strip(),
            is_approved=True,
        )
        await self.db.commit()
        await self.db.refresh(c)
        return c

    async def react(
        self, *, user: User, target_type: str, target_id: int, reaction: str,
    ) -> dict[str, int]:
        if target_type == "question":
            if await self.questions.get(target_id) is None:
                raise NotFound("Question not found")
        elif target_type == "comment":
            if await self.comments.get(target_id) is None:
                raise NotFound("Comment not found")
        else:
            raise NotFound("Unknown target")
        await self.reactions.toggle(
            user_id=user.id, target_type=target_type, target_id=target_id, reaction=reaction,
        )
        await self.db.commit()
        counts = await self.reactions.counts(target_type, [target_id])
        return counts.get(target_id, {})

    async def reaction_counts(
        self, target_type: str, target_ids: list[int],
    ) -> dict[int, dict[str, int]]:
        return await self.reactions.counts(target_type, target_ids)
