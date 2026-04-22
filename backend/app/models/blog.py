from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class BlogCategory(Base):
    __tablename__ = "blog_categories"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)

    posts: Mapped[list["BlogPost"]] = relationship(back_populates="category")


class BlogPost(Base):
    __tablename__ = "blog_posts"

    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    excerpt: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    content_md: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cover_url: Mapped[str | None] = mapped_column(String(400))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("blog_categories.id"))
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    category: Mapped["BlogCategory | None"] = relationship(back_populates="posts", lazy="joined")
