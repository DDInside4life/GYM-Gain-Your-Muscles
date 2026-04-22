from __future__ import annotations

from markdown_it import MarkdownIt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import Conflict, NotFound
from app.models.blog import BlogPost
from app.repositories.blog import BlogCategoryRepository, BlogPostRepository
from app.schemas.blog import BlogPostCreate, BlogPostUpdate

_md = MarkdownIt("commonmark", {"breaks": True, "linkify": True}).enable("table")


def render_md(text: str) -> str:
    return _md.render(text or "")


class BlogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.posts = BlogPostRepository(db)
        self.categories = BlogCategoryRepository(db)

    async def create_post(self, data: BlogPostCreate, author_id: int | None) -> BlogPost:
        if await self.posts.get_by_slug(data.slug):
            raise Conflict("Slug already exists")
        post = await self.posts.create(**data.model_dump(), author_id=author_id)
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def update_post(self, slug: str, data: BlogPostUpdate) -> BlogPost:
        post = await self.posts.get_by_slug(slug)
        if not post:
            raise NotFound("Post not found")
        await self.posts.update(post, **data.model_dump(exclude_unset=True))
        await self.db.commit()
        await self.db.refresh(post)
        return post

    async def delete_post(self, slug: str) -> None:
        post = await self.posts.get_by_slug(slug)
        if not post:
            raise NotFound("Post not found")
        await self.posts.delete(post)
        await self.db.commit()
