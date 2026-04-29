"""user profile extensions and workout generation config

Adds:
  - users.global_restrictions (text[])
  - users.priority_exercise_ids (int[])
  - workout_questionnaires.priority_exercise_ids (int[])
  - workout_questionnaires.session_duration_min (int, nullable)
  - workout_questionnaires.training_structure (text, nullable)
  - workout_questionnaires.periodization (text, nullable)
  - workout_questionnaires.cycle_length_weeks (int, nullable)

All columns are backward-compatible with sane defaults.

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-29 01:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "global_restrictions",
            postgresql.ARRAY(sa.String(length=40)),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "priority_exercise_ids",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default="{}",
        ),
    )

    op.add_column(
        "workout_questionnaires",
        sa.Column(
            "priority_exercise_ids",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "workout_questionnaires",
        sa.Column("session_duration_min", sa.Integer(), nullable=True),
    )
    op.add_column(
        "workout_questionnaires",
        sa.Column("training_structure", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "workout_questionnaires",
        sa.Column("periodization", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "workout_questionnaires",
        sa.Column("cycle_length_weeks", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workout_questionnaires", "cycle_length_weeks")
    op.drop_column("workout_questionnaires", "periodization")
    op.drop_column("workout_questionnaires", "training_structure")
    op.drop_column("workout_questionnaires", "session_duration_min")
    op.drop_column("workout_questionnaires", "priority_exercise_ids")

    op.drop_column("users", "priority_exercise_ids")
    op.drop_column("users", "global_restrictions")
