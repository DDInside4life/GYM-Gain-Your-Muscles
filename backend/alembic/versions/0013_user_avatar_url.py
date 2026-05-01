"""add avatar url to user profile

Revision ID: 0013
Revises: 0012
Create Date: 2026-04-30 00:34:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(length=400), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
