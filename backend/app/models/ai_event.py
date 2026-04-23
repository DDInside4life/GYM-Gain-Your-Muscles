from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AIEvent(Base):
    """Audit log for every agent run.

    Powers:
      - explanation retrieval for old plans (GET /ai/plans/{id}/explanation)
      - debugging LLM regressions
      - future offline learning (RL / supervised scoring)
    """
    __tablename__ = "ai_events"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    model: Mapped[str | None] = mapped_column(String(120))

    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="SET NULL"), index=True,
    )
    nutrition_plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("nutrition_plans.id", ondelete="SET NULL"), index=True,
    )

    prompt: Mapped[str | None] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text)
    output: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    explanation: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(String(500))
