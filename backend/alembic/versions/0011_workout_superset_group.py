"""workout exercise superset group

Adds:
  - workout_exercises.superset_group (int, nullable) — pairs exercises that
    must be performed back-to-back (antagonist supersets) when ``pack_session``
    decides to compress a day to fit a duration cap.

Revision ID: 0011
Revises: 0010
Create Date: 2026-04-29 20:30:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "workout_exercises",
        sa.Column("superset_group", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workout_exercises", "superset_group")
