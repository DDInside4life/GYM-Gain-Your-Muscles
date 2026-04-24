"""workout templates

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-23 16:20:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workout_templates",
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("split_type", sa.String(length=40), nullable=False),
        sa.Column("days_per_week", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_workout_templates_slug"),
    )
    op.create_index("ix_workout_templates_slug", "workout_templates", ["slug"], unique=False)

    op.create_table(
        "template_days",
        sa.Column("template_id", sa.Integer(), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("focus", sa.String(length=120), nullable=False),
        sa.Column("is_rest", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["template_id"], ["workout_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "day_index", name="uq_template_days_template_day"),
    )
    op.create_index("ix_template_days_template_id", "template_days", ["template_id"], unique=False)

    op.create_table(
        "template_exercises",
        sa.Column("template_day_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps_min", sa.Integer(), nullable=False),
        sa.Column("reps_max", sa.Integer(), nullable=False),
        sa.Column("rest_sec", sa.Integer(), nullable=False),
        sa.Column("target_percent_1rm", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(length=240), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["template_day_id"], ["template_days.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_day_id", "position", name="uq_template_exercises_day_pos"),
    )
    op.create_index("ix_template_exercises_template_day_id", "template_exercises", ["template_day_id"], unique=False)
    op.create_index("ix_template_exercises_exercise_id", "template_exercises", ["exercise_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_template_exercises_exercise_id", table_name="template_exercises")
    op.drop_index("ix_template_exercises_template_day_id", table_name="template_exercises")
    op.drop_table("template_exercises")
    op.drop_index("ix_template_days_template_id", table_name="template_days")
    op.drop_table("template_days")
    op.drop_index("ix_workout_templates_slug", table_name="workout_templates")
    op.drop_table("workout_templates")
