from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import NotFound
from app.repositories.forum import ForumQuestionRepository
from app.schemas.forum import (
    ForumCommentCreate, ForumCommentRead, ForumQuestionCreate,
    ForumQuestionDetail, ForumQuestionRead, ReactionCounts, ReactionInput,
)
from app.services.forum import ForumService

router = APIRouter()


@router.get("/questions", response_model=list[ForumQuestionRead])
async def list_questions(
    db: DbSession, limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0),
) -> list[ForumQuestionRead]:
    repo = ForumQuestionRepository(db)
    qs = await repo.list_approved(limit=limit, offset=offset)
    counts = await ForumService(db).reaction_counts("question", [q.id for q in qs])
    out: list[ForumQuestionRead] = []
    for q in qs:
        data = ForumQuestionRead.model_validate(q)
        data.reactions = counts.get(q.id, {})
        out.append(data)
    return out


@router.get("/questions/{qid}", response_model=ForumQuestionDetail)
async def get_question(qid: int, db: DbSession) -> ForumQuestionDetail:
    repo = ForumQuestionRepository(db)
    q = await repo.get_with_comments(qid)
    if q is None or not q.is_approved:
        raise NotFound("Question not found")
    service = ForumService(db)
    q_counts = (await service.reaction_counts("question", [q.id])).get(q.id, {})
    c_counts = await service.reaction_counts("comment", [c.id for c in q.comments])

    detail = ForumQuestionDetail.model_validate(q)
    detail.reactions = q_counts
    detail.comments = []
    for c in q.comments:
        cread = ForumCommentRead.model_validate(c)
        cread.reactions = c_counts.get(c.id, {})
        detail.comments.append(cread)
    return detail


@router.post("/questions", response_model=ForumQuestionRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    data: ForumQuestionCreate, user: CurrentUser, db: DbSession,
) -> ForumQuestionRead:
    q = await ForumService(db).create_question(user, data)
    return ForumQuestionRead.model_validate(q)


@router.post("/questions/{qid}/react", response_model=ReactionCounts)
async def react_question(
    qid: int, data: ReactionInput, user: CurrentUser, db: DbSession,
) -> ReactionCounts:
    counts = await ForumService(db).react(
        user=user, target_type="question", target_id=qid, reaction=data.reaction,
    )
    return ReactionCounts(reactions=counts)


@router.post(
    "/questions/{qid}/comments",
    response_model=ForumCommentRead, status_code=status.HTTP_201_CREATED,
)
async def comment(
    qid: int, data: ForumCommentCreate, user: CurrentUser, db: DbSession,
) -> ForumCommentRead:
    c = await ForumService(db).add_comment(user, qid, data)
    return ForumCommentRead.model_validate(c)


@router.post("/comments/{cid}/react", response_model=ReactionCounts)
async def react_comment(
    cid: int, data: ReactionInput, user: CurrentUser, db: DbSession,
) -> ReactionCounts:
    counts = await ForumService(db).react(
        user=user, target_type="comment", target_id=cid, reaction=data.reaction,
    )
    return ReactionCounts(reactions=counts)
