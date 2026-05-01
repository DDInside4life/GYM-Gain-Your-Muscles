from __future__ import annotations

from sqlalchemy import desc, select

from app.models.blog import BlogCategory, BlogPost
from app.repositories.base import BaseRepository


class BlogCategoryRepository(BaseRepository[BlogCategory]):
    model = BlogCategory

    async def get_by_slug(self, slug: str) -> BlogCategory | None:
        res = await self.db.execute(select(BlogCategory).where(BlogCategory.slug == slug))
        return res.scalar_one_or_none()


class BlogPostRepository(BaseRepository[BlogPost]):
    model = BlogPost

    async def get_by_slug(self, slug: str) -> BlogPost | None:
        res = await self.db.execute(select(BlogPost).where(BlogPost.slug == slug))
        return res.scalar_one_or_none()

    async def list_published(self, limit: int = 20, offset: int = 0) -> list[BlogPost]:
        stmt = (
            select(BlogPost)
            .where(BlogPost.is_published.is_(True))
            .order_by(desc(BlogPost.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[BlogPost]:
        stmt = (
            select(BlogPost)
            .order_by(desc(BlogPost.created_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
