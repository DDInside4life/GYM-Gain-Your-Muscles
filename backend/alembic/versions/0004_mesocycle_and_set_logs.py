"""mesocycle and set logs

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-23 00:30:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mesocycles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cycle_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("current_week", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("weekly_volume", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.UniqueConstraint("plan_id", name="uq_mesocycle_plan"),
    )
    op.create_index("ix_mesocycles_user_id", "mesocycles", ["user_id"])
    op.create_index("ix_mesocycle_user_active", "mesocycles", ["user_id", "is_active"])

    op.create_table(
        "set_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_id", sa.Integer(), sa.ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workout_exercise_id", sa.Integer(), sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_index", sa.Integer(), nullable=False),
        sa.Column("set_index", sa.Integer(), nullable=False),
        sa.Column("planned_weight_kg", sa.Float(), nullable=True),
        sa.Column("completed_reps", sa.Integer(), nullable=False),
        sa.Column("completed_weight_kg", sa.Float(), nullable=False),
        sa.Column("rir", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("estimated_1rm", sa.Float(), nullable=False),
    )
    op.create_index("ix_set_logs_user_id", "set_logs", ["user_id"])
    op.create_index("ix_set_logs_plan_id", "set_logs", ["plan_id"])
    op.create_index("ix_set_logs_day_id", "set_logs", ["day_id"])
    op.create_index("ix_set_logs_workout_exercise_id", "set_logs", ["workout_exercise_id"])
    op.create_index("ix_set_logs_exercise_id", "set_logs", ["exercise_id"])
    op.create_index("ix_set_logs_user_created", "set_logs", ["user_id", "created_at"])
    op.create_index("ix_set_logs_plan_week", "set_logs", ["plan_id", "week_index"])


def downgrade() -> None:
    op.drop_index("ix_set_logs_plan_week", table_name="set_logs")
    op.drop_index("ix_set_logs_user_created", table_name="set_logs")
    op.drop_index("ix_set_logs_exercise_id", table_name="set_logs")
    op.drop_index("ix_set_logs_workout_exercise_id", table_name="set_logs")
    op.drop_index("ix_set_logs_day_id", table_name="set_logs")
    op.drop_index("ix_set_logs_plan_id", table_name="set_logs")
    op.drop_index("ix_set_logs_user_id", table_name="set_logs")
    op.drop_table("set_logs")

    op.drop_index("ix_mesocycle_user_active", table_name="mesocycles")
    op.drop_index("ix_mesocycles_user_id", table_name="mesocycles")
    op.drop_table("mesocycles")
