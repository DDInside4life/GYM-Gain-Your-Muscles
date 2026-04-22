from __future__ import annotations

from fastapi import APIRouter, Query, Response, status

from app.core.deps import CurrentAdmin, DbSession
from app.core.exceptions import NotFound
from app.repositories.blog import BlogCategoryRepository, BlogPostRepository
from app.schemas.blog import (
    BlogCategoryCreate, BlogCategoryRead, BlogPostCreate, BlogPostRead, BlogPostUpdate,
)
from app.services.blog import BlogService, render_md

router = APIRouter()


def _to_read(post) -> BlogPostRead:
    data = BlogPostRead.model_validate(post)
    data.content_html = render_md(post.content_md or "")
    return data


@router.get("/posts", response_model=list[BlogPostRead])
async def list_posts(db: DbSession, limit: int = Query(20, le=100), offset: int = 0) -> list[BlogPostRead]:
    posts = await BlogPostRepository(db).list_published(limit=limit, offset=offset)
    return [_to_read(p) for p in posts]


@router.get("/posts/{slug}", response_model=BlogPostRead)
async def get_post(slug: str, db: DbSession) -> BlogPostRead:
    post = await BlogPostRepository(db).get_by_slug(slug)
    if not post:
        raise NotFound("Post not found")
    return _to_read(post)


@router.post("/posts", response_model=BlogPostRead, status_code=status.HTTP_201_CREATED)
async def create_post(data: BlogPostCreate, admin: CurrentAdmin, db: DbSession) -> BlogPostRead:
    post = await BlogService(db).create_post(data, admin.id)
    return _to_read(post)


@router.put("/posts/{slug}", response_model=BlogPostRead)
async def update_post(slug: str, data: BlogPostUpdate, _: CurrentAdmin, db: DbSession) -> BlogPostRead:
    post = await BlogService(db).update_post(slug, data)
    return _to_read(post)


@router.delete(
    "/posts/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_post(slug: str, _: CurrentAdmin, db: DbSession) -> Response:
    await BlogService(db).delete_post(slug)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/categories", response_model=list[BlogCategoryRead])
async def list_categories(db: DbSession) -> list[BlogCategoryRead]:
    cats = await BlogCategoryRepository(db).list(limit=200)
    return [BlogCategoryRead.model_validate(c) for c in cats]


@router.post("/categories", response_model=BlogCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(data: BlogCategoryCreate, _: CurrentAdmin, db: DbSession) -> BlogCategoryRead:
    repo = BlogCategoryRepository(db)
    cat = await repo.create(**data.model_dump())
    await db.commit()
    await db.refresh(cat)
    return BlogCategoryRead.model_validate(cat)
