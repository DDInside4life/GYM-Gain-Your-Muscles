"""exercise russian naming fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-23 01:30:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("name_ru", sa.String(length=120), nullable=True))
    op.add_column("exercises", sa.Column("name_en", sa.String(length=120), nullable=True))
    op.execute("UPDATE exercises SET name_ru = name WHERE name_ru IS NULL")
    op.alter_column("exercises", "name_ru", nullable=False)
    op.create_index("ix_exercises_name_ru", "exercises", ["name_ru"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_exercises_name_ru", table_name="exercises")
    op.drop_column("exercises", "name_en")
    op.drop_column("exercises", "name_ru")
