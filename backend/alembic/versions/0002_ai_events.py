"""ai events table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-22 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("model", sa.String(120)),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="SET NULL")),
        sa.Column("nutrition_plan_id", sa.Integer(), sa.ForeignKey("nutrition_plans.id", ondelete="SET NULL")),
        sa.Column("prompt", sa.Text()),
        sa.Column("response", sa.Text()),
        sa.Column("output", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("explanation", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.String(500)),
    )
    op.create_index("ix_ai_events_user_id", "ai_events", ["user_id"])
    op.create_index("ix_ai_events_plan_id", "ai_events", ["plan_id"])
    op.create_index("ix_ai_events_nutrition_plan_id", "ai_events", ["nutrition_plan_id"])
    op.create_index("ix_ai_events_kind", "ai_events", ["kind"])
    op.create_index("ix_ai_events_user_kind_created", "ai_events", ["user_id", "kind", sa.text("created_at DESC")])


def downgrade() -> None:
    op.drop_table("ai_events")
