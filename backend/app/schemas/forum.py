from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TimestampMixin


class ForumQuestionBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(default="", max_length=5000)
    tags: list[str] = Field(default_factory=list, max_length=10)


class ForumQuestionCreate(ForumQuestionBase):
    pass


class ForumCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parent_id: int | None = Field(default=None, gt=0)


class ForumCommentRead(ORMModel, TimestampMixin):
    question_id: int
    parent_id: int | None
    user_id: int | None
    body: str
    is_approved: bool
    reactions: dict[str, int] = Field(default_factory=dict)


class ForumQuestionRead(ORMModel, TimestampMixin):
    user_id: int | None
    title: str
    body: str
    tags: list[str]
    is_approved: bool
    reactions: dict[str, int] = Field(default_factory=dict)


class ForumQuestionDetail(ForumQuestionRead):
    comments: list[ForumCommentRead] = Field(default_factory=list)


class ReactionInput(BaseModel):
    reaction: str = Field(pattern=r"^[a-z_]{1,24}$")


class ReactionCounts(BaseModel):
    reactions: dict[str, int]
