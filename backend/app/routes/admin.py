from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentAdmin, DbSession
from app.core.exceptions import NotFound
from app.repositories.forum import ForumCommentRepository, ForumQuestionRepository
from app.services.admin import AdminService

router = APIRouter()

_NO_CONTENT = Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/analytics")
async def analytics(_: CurrentAdmin, db: DbSession) -> dict:
    return await AdminService(db).analytics()


@router.post("/forum/questions/{qid}/approve")
async def approve_question(qid: int, _: CurrentAdmin, db: DbSession) -> dict:
    q = await ForumQuestionRepository(db).get(qid)
    if not q:
        raise NotFound("Not found")
    q.is_approved = True
    await db.commit()
    return {"ok": True}


@router.delete(
    "/forum/questions/{qid}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_question(qid: int, _: CurrentAdmin, db: DbSession) -> Response:
    repo = ForumQuestionRepository(db)
    q = await repo.get(qid)
    if not q:
        raise NotFound("Not found")
    await repo.delete(q)
    await db.commit()
    return _NO_CONTENT


@router.delete(
    "/forum/comments/{cid}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_comment(cid: int, _: CurrentAdmin, db: DbSession) -> Response:
    repo = ForumCommentRepository(db)
    c = await repo.get(cid)
    if not c:
        raise NotFound("Not found")
    await repo.delete(c)
    await db.commit()
    return _NO_CONTENT
