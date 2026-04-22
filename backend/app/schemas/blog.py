from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TimestampMixin


class BlogCategoryBase(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)


class BlogCategoryCreate(BlogCategoryBase):
    pass


class BlogCategoryRead(ORMModel, TimestampMixin, BlogCategoryBase):
    pass


class BlogPostBase(BaseModel):
    slug: str = Field(min_length=1, max_length=140)
    title: str = Field(min_length=1, max_length=200)
    excerpt: str = ""
    content_md: str = ""
    cover_url: str | None = None
    is_published: bool = True
    category_id: int | None = None


class BlogPostCreate(BlogPostBase):
    pass


class BlogPostUpdate(BaseModel):
    title: str | None = None
    excerpt: str | None = None
    content_md: str | None = None
    cover_url: str | None = None
    is_published: bool | None = None
    category_id: int | None = None


class BlogPostRead(ORMModel, TimestampMixin, BlogPostBase):
    category: BlogCategoryRead | None = None
    content_html: str = ""
