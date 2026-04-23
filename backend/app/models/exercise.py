from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MuscleGroup(str, enum.Enum):
    chest = "chest"
    back = "back"
    legs = "legs"
    glutes = "glutes"
    shoulders = "shoulders"
    biceps = "biceps"
    triceps = "triceps"
    core = "core"
    calves = "calves"
    forearms = "forearms"
    full_body = "full_body"
    cardio = "cardio"


class Equipment(str, enum.Enum):
    bodyweight = "bodyweight"
    barbell = "barbell"
    dumbbell = "dumbbell"
    machine = "machine"
    cable = "cable"
    kettlebell = "kettlebell"
    bands = "bands"


class ExerciseCategory(str, enum.Enum):
    compound = "compound"
    isolation = "isolation"
    cardio = "cardio"
    mobility = "mobility"


class Exercise(Base):
    __tablename__ = "exercises"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name_ru: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    primary_muscle: Mapped[MuscleGroup] = mapped_column(
        Enum(MuscleGroup, name="muscle_group"), nullable=False,
    )
    secondary_muscles: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), default=list, nullable=False,
    )
    equipment: Mapped[Equipment] = mapped_column(
        Enum(Equipment, name="equipment"), nullable=False,
    )
    category: Mapped[ExerciseCategory] = mapped_column(
        Enum(ExerciseCategory, name="exercise_category"), nullable=False,
    )

    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1..5
    contraindications: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), default=list, nullable=False,
    )
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(400))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
