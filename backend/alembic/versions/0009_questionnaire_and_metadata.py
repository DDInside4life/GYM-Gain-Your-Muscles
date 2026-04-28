"""workout questionnaire, exercise metadata, workout_exercise RIR

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-28 23:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("movement_archetype", sa.String(length=40), nullable=False, server_default="generic"),
    )
    op.add_column("exercises", sa.Column("is_home", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("exercises", sa.Column("is_gym", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("exercises", sa.Column("suitable_for_test", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column(
        "exercises",
        sa.Column("suitable_for_progression", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_exercises_archetype", "exercises", ["movement_archetype"], unique=False)

    op.add_column("workout_exercises", sa.Column("target_rir", sa.Float(), nullable=True))
    op.add_column(
        "workout_exercises",
        sa.Column("rpe_text", sa.String(length=200), nullable=False, server_default=""),
    )

    op.create_table(
        "workout_questionnaires",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sex", sa.String(length=10), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("height_cm", sa.Float(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("experience", sa.String(length=20), nullable=False),
        sa.Column("goal", sa.String(length=20), nullable=False),
        sa.Column("location", sa.String(length=10), nullable=False),
        sa.Column("equipment", postgresql.ARRAY(sa.String(length=40)), nullable=False, server_default="{}"),
        sa.Column("injuries", postgresql.ARRAY(sa.String(length=40)), nullable=False, server_default="{}"),
        sa.Column("days_per_week", sa.Integer(), nullable=False),
        sa.Column("available_days", postgresql.ARRAY(sa.String(length=3)), nullable=False, server_default="{}"),
        sa.Column("notes", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("config", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_workout_questionnaires_user_id", "workout_questionnaires", ["user_id"])
    op.create_index(
        "ix_workout_questionnaires_user_created",
        "workout_questionnaires",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_workout_questionnaires_user_created", table_name="workout_questionnaires")
    op.drop_index("ix_workout_questionnaires_user_id", table_name="workout_questionnaires")
    op.drop_table("workout_questionnaires")

    op.drop_column("workout_exercises", "rpe_text")
    op.drop_column("workout_exercises", "target_rir")

    op.drop_index("ix_exercises_archetype", table_name="exercises")
    op.drop_column("exercises", "suitable_for_progression")
    op.drop_column("exercises", "suitable_for_test")
    op.drop_column("exercises", "is_gym")
    op.drop_column("exercises", "is_home")
    op.drop_column("exercises", "movement_archetype")
