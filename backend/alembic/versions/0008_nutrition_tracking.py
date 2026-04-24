"""nutrition tracking meals and food entries

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-24 10:30:00
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "nutrition_meals",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nutrition_meals_user_id", "nutrition_meals", ["user_id"], unique=False)
    op.create_index("ix_nutrition_meals_date", "nutrition_meals", ["date"], unique=False)
    op.create_index("ix_nutrition_meals_user_date", "nutrition_meals", ["user_id", "date"], unique=False)

    op.create_table(
        "food_entries",
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=140), nullable=False),
        sa.Column("protein_per_100g", sa.Float(), nullable=False),
        sa.Column("fat_per_100g", sa.Float(), nullable=False),
        sa.Column("carbs_per_100g", sa.Float(), nullable=False),
        sa.Column("grams", sa.Float(), nullable=False),
        sa.Column("calculated_protein", sa.Float(), nullable=False),
        sa.Column("calculated_fat", sa.Float(), nullable=False),
        sa.Column("calculated_carbs", sa.Float(), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["meal_id"], ["nutrition_meals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_entries_meal_id", "food_entries", ["meal_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_food_entries_meal_id", table_name="food_entries")
    op.drop_table("food_entries")
    op.drop_index("ix_nutrition_meals_user_date", table_name="nutrition_meals")
    op.drop_index("ix_nutrition_meals_date", table_name="nutrition_meals")
    op.drop_index("ix_nutrition_meals_user_id", table_name="nutrition_meals")
    op.drop_table("nutrition_meals")
