from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ForumQuestion(Base):
    __tablename__ = "forum_questions"

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    comments: Mapped[list["ForumComment"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="ForumComment.created_at",
    )
    reactions: Mapped[list["ForumReaction"]] = relationship(
        primaryjoin="and_(ForumReaction.target_type=='question', "
                    "foreign(ForumReaction.target_id)==ForumQuestion.id)",
        viewonly=True,
    )


class ForumComment(Base):
    __tablename__ = "forum_comments"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("forum_questions.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("forum_comments.id", ondelete="CASCADE"), index=True,
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    question: Mapped["ForumQuestion"] = relationship(back_populates="comments")


class ForumReaction(Base):
    __tablename__ = "forum_reactions"
    __table_args__ = (
        UniqueConstraint("user_id", "target_type", "target_id", "reaction", name="uq_forum_reactions"),
        CheckConstraint("target_type in ('question','comment')", name="ck_forum_reactions_target"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_id: Mapped[int] = mapped_column(nullable=False, index=True)
    reaction: Mapped[str] = mapped_column(String(24), nullable=False)
