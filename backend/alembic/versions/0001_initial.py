"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-21 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    enums = {
        "user_sex": ("male", "female"),
        "user_experience": ("beginner", "intermediate", "advanced"),
        "user_goal": ("muscle_gain", "fat_loss", "strength", "endurance", "general"),
        "muscle_group": (
            "chest", "back", "legs", "glutes", "shoulders", "biceps", "triceps",
            "core", "calves", "forearms", "full_body", "cardio",
        ),
        "equipment": ("bodyweight", "barbell", "dumbbell", "machine", "cable", "kettlebell", "bands"),
        "exercise_category": ("compound", "isolation", "cardio", "mobility"),
        "workout_difficulty": ("very_easy", "easy", "ok", "hard", "very_hard"),
    }
    for name, values in enums.items():
        labels = ", ".join(f"'{v}'" for v in values)
        op.execute(
            f"DO $$ BEGIN "
            f"IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN "
            f"CREATE TYPE {name} AS ENUM ({labels}); "
            f"END IF; END $$;"
        )

    def enum(name: str) -> postgresql.ENUM:
        return postgresql.ENUM(*enums[name], name=name, create_type=False)

    op.create_table(
        "users",
        *_ts_cols(),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(120)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sex", enum("user_sex")),
        sa.Column("birth_date", sa.Date()),
        sa.Column("height_cm", sa.Float()),
        sa.Column("weight_kg", sa.Float()),
        sa.Column("experience", enum("user_experience")),
        sa.Column("goal", enum("user_goal")),
        sa.Column("activity_factor", sa.Float(), nullable=False, server_default="1.55"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "exercises",
        *_ts_cols(),
        sa.Column("slug", sa.String(80), unique=True, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("primary_muscle", enum("muscle_group"), nullable=False),
        sa.Column("secondary_muscles", postgresql.ARRAY(sa.String(40)), nullable=False, server_default="{}"),
        sa.Column("equipment", enum("equipment"), nullable=False),
        sa.Column("category", enum("exercise_category"), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("contraindications", postgresql.ARRAY(sa.String(40)), nullable=False, server_default="{}"),
        sa.Column("meta", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("image_url", sa.String(400)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_exercises_slug", "exercises", ["slug"], unique=True)
    op.create_index("ix_exercises_muscle_active", "exercises", ["primary_muscle", "is_active"])

    op.create_table(
        "workout_plans",
        *_ts_cols(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False, server_default="Weekly Plan"),
        sa.Column("week_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("split_type", sa.String(40), nullable=False, server_default="full_body"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("params", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_workout_plans_user_id", "workout_plans", ["user_id"])
    op.create_index("ix_workout_plans_user_active_week", "workout_plans", ["user_id", "is_active", "week_number"])

    op.create_table(
        "workout_days",
        *_ts_cols(),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(60), nullable=False),
        sa.Column("focus", sa.String(60), nullable=False, server_default=""),
        sa.Column("is_rest", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("plan_id", "day_index", name="uq_workout_days_plan_day"),
    )
    op.create_index("ix_workout_days_plan_id", "workout_days", ["plan_id"])

    op.create_table(
        "workout_exercises",
        *_ts_cols(),
        sa.Column("day_id", sa.Integer(), sa.ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", sa.Integer(), sa.ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sets", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("reps_min", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("reps_max", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("weight_kg", sa.Float()),
        sa.Column("rest_sec", sa.Integer(), nullable=False, server_default="90"),
        sa.Column("notes", sa.String(240), nullable=False, server_default=""),
    )
    op.create_index("ix_workout_exercises_day_id", "workout_exercises", ["day_id"])
    op.create_index("ix_workout_exercises_exercise_id", "workout_exercises", ["exercise_id"])

    op.create_table(
        "workout_feedback",
        *_ts_cols(),
        sa.Column("day_id", sa.Integer(), sa.ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("difficulty", enum("workout_difficulty"), nullable=False, server_default="ok"),
        sa.Column("discomfort", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.UniqueConstraint("day_id", "user_id", name="uq_workout_feedback_day_user"),
    )
    op.create_index("ix_workout_feedback_day_id", "workout_feedback", ["day_id"])
    op.create_index("ix_workout_feedback_user_id", "workout_feedback", ["user_id"])

    op.create_table(
        "nutrition_plans",
        *_ts_cols(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Integer(), nullable=False),
        sa.Column("fat_g", sa.Integer(), nullable=False),
        sa.Column("carbs_g", sa.Integer(), nullable=False),
        sa.Column("bmr", sa.Integer(), nullable=False),
        sa.Column("tdee", sa.Integer(), nullable=False),
        sa.Column("goal_label", sa.String(40), nullable=False),
    )
    op.create_index("ix_nutrition_plans_user_id", "nutrition_plans", ["user_id"])

    op.create_table(
        "meals",
        *_ts_cols(),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("nutrition_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("protein_g", sa.Float(), nullable=False),
        sa.Column("fat_g", sa.Float(), nullable=False),
        sa.Column("carbs_g", sa.Float(), nullable=False),
        sa.Column("items", postgresql.JSONB(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_meals_plan_id", "meals", ["plan_id"])

    op.create_table(
        "blog_categories",
        *_ts_cols(),
        sa.Column("slug", sa.String(80), unique=True, nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
    )
    op.create_index("ix_blog_categories_slug", "blog_categories", ["slug"], unique=True)

    op.create_table(
        "blog_posts",
        *_ts_cols(),
        sa.Column("slug", sa.String(140), unique=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("excerpt", sa.String(500), nullable=False, server_default=""),
        sa.Column("content_md", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_url", sa.String(400)),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("blog_categories.id", ondelete="SET NULL")),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
    )
    op.create_index("ix_blog_posts_slug", "blog_posts", ["slug"], unique=True)
    op.create_index("ix_blog_posts_pub_created", "blog_posts", ["is_published", sa.text("created_at DESC")])

    op.create_table(
        "forum_questions",
        *_ts_cols(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_forum_questions_user_id", "forum_questions", ["user_id"])
    op.create_index("ix_forum_questions_approved_created", "forum_questions",
                    ["is_approved", sa.text("created_at DESC")])

    op.create_table(
        "forum_comments",
        *_ts_cols(),
        sa.Column("question_id", sa.Integer(), sa.ForeignKey("forum_questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Integer(), sa.ForeignKey("forum_comments.id", ondelete="CASCADE")),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_forum_comments_question_id", "forum_comments", ["question_id"])
    op.create_index("ix_forum_comments_parent_id", "forum_comments", ["parent_id"])
    op.create_index("ix_forum_comments_user_id", "forum_comments", ["user_id"])

    op.create_table(
        "forum_reactions",
        *_ts_cols(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=False),
        sa.Column("reaction", sa.String(24), nullable=False),
        sa.UniqueConstraint("user_id", "target_type", "target_id", "reaction", name="uq_forum_reactions"),
        sa.CheckConstraint("target_type in ('question','comment')", name="ck_forum_reactions_target"),
    )
    op.create_index("ix_forum_reactions_user_id", "forum_reactions", ["user_id"])
    op.create_index("ix_forum_reactions_target", "forum_reactions", ["target_type", "target_id"])

    op.create_table(
        "weight_entries",
        *_ts_cols(),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.Date(), nullable=False),
        sa.UniqueConstraint("user_id", "recorded_at", name="uq_weight_entries_user_date"),
    )
    op.create_index("ix_weight_entries_user_id", "weight_entries", ["user_id"])
    op.create_index("ix_weight_entries_user_date", "weight_entries", ["user_id", "recorded_at"])


def downgrade() -> None:
    for table in [
        "weight_entries", "forum_reactions", "forum_comments", "forum_questions",
        "blog_posts", "blog_categories", "meals", "nutrition_plans",
        "workout_feedback", "workout_exercises", "workout_days", "workout_plans",
        "exercises", "users",
    ]:
        op.drop_table(table)
    for enum_name in [
        "workout_difficulty", "exercise_category", "equipment",
        "muscle_group", "user_goal", "user_experience", "user_sex",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
