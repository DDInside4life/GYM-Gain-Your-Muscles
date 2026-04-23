"""month program + workout results

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-23 00:00:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'program_phase') THEN "
        "CREATE TYPE program_phase AS ENUM ('test', 'work'); "
        "END IF; END $$;"
    )

    phase_enum = postgresql.ENUM("test", "work", name="program_phase", create_type=False)

    op.add_column("workout_plans", sa.Column("month_index", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("workout_plans", sa.Column("cycle_week", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("workout_plans", sa.Column("phase", phase_enum, nullable=False, server_default="test"))

    op.add_column("workout_days", sa.Column("week_index", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("workout_days", sa.Column("phase", phase_enum, nullable=False, server_default="work"))

    op.add_column("workout_exercises", sa.Column("target_percent_1rm", sa.Float()))
    op.add_column("workout_exercises", sa.Column("is_test_set", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("workout_exercises", sa.Column("test_instruction", sa.String(240), nullable=False, server_default=""))

    op.create_table(
        "workout_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_id", sa.Integer(), sa.ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workout_exercise_id", sa.Integer(), sa.ForeignKey("workout_exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False),
        sa.Column("week_index", sa.Integer(), nullable=False),
        sa.Column("reps_completed", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("estimated_1rm", sa.Float(), nullable=False),
        sa.UniqueConstraint("workout_exercise_id", "user_id", name="uq_workout_result_exercise_user"),
    )
    op.create_index("ix_workout_results_user_id", "workout_results", ["user_id"])
    op.create_index("ix_workout_results_plan_id", "workout_results", ["plan_id"])
    op.create_index("ix_workout_results_day_id", "workout_results", ["day_id"])
    op.create_index("ix_workout_results_workout_exercise_id", "workout_results", ["workout_exercise_id"])
    op.create_index("ix_workout_results_exercise_id", "workout_results", ["exercise_id"])


def downgrade() -> None:
    op.drop_table("workout_results")

    op.drop_column("workout_exercises", "test_instruction")
    op.drop_column("workout_exercises", "is_test_set")
    op.drop_column("workout_exercises", "target_percent_1rm")

    op.drop_column("workout_days", "phase")
    op.drop_column("workout_days", "week_index")

    op.drop_column("workout_plans", "phase")
    op.drop_column("workout_plans", "cycle_week")
    op.drop_column("workout_plans", "month_index")

    op.execute("DROP TYPE IF EXISTS program_phase")
