from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi
from typing import Literal

from app.models.user import Experience
from app.services.workout.splits import pick_split

LoadMode = Literal["percent_1rm", "absolute"]


@dataclass(frozen=True, slots=True)
class CurveParams:
    start_kpsh: float
    weeks: int
    growth_step: float = 0.08
    drop_step: float = 0.15
    wave_length: int = 4


@dataclass(frozen=True, slots=True)
class WeeklyTarget:
    week: int
    kpsh: float
    intensity: float
    tonnage: float
    intensity_pct_1rm: float
    phase: str


class LoadModel:
    def generate_kpsh_curve(
        self,
        start_kpsh: float,
        weeks: int,
        growth_step: float,
        drop_step: float,
        wave_length: int = 4,
    ) -> list[float]:
        if weeks <= 0:
            return []
        base = max(1.0, start_kpsh)
        values: list[float] = []
        for idx in range(weeks):
            wave_pos = idx % max(2, wave_length)
            cycle = idx // max(2, wave_length)
            growth_factor = 1.0 + (cycle * growth_step)
            up = wave_pos < (wave_length - 1)
            wave_scale = 1.0 + (growth_step * wave_pos) if up else 1.0 - drop_step
            values.append(round(base * growth_factor * max(0.55, wave_scale), 2))
        return values

    def generate_intensity_curve(
        self,
        start_weight: float,
        weeks: int,
        wave_length: int = 4,
        amplitude: float = 0.14,
    ) -> list[float]:
        if weeks <= 0:
            return []
        base = max(20.0, start_weight)
        values: list[float] = []
        for idx in range(weeks):
            angle = (2 * pi * (idx % max(2, wave_length))) / max(2, wave_length)
            inverse_wave = 1 - (amplitude * cos(angle))
            values.append(round(base * max(0.7, inverse_wave), 2))
        return values


class TrainingEngine:
    def __init__(self, load_model: LoadModel | None = None) -> None:
        self.load_model = load_model or LoadModel()

    @staticmethod
    def choose_split(training_days: int, experience: Experience) -> str:
        return pick_split(training_days, experience)

    @staticmethod
    def estimate_1rm(weight: float, reps: int) -> float:
        return round(weight * (1 + reps / 30.0), 2)

    def build_targets(
        self,
        *,
        start_kpsh: float,
        start_weight: float,
        weeks: int,
        growth_step: float = 0.08,
        drop_step: float = 0.15,
        wave_length: int = 4,
        load_mode: LoadMode = "percent_1rm",
    ) -> list[WeeklyTarget]:
        kpsh_curve = self.load_model.generate_kpsh_curve(
            start_kpsh=start_kpsh,
            weeks=weeks,
            growth_step=growth_step,
            drop_step=drop_step,
            wave_length=wave_length,
        )
        intensity_curve = self.load_model.generate_intensity_curve(
            start_weight=start_weight,
            weeks=weeks,
            wave_length=wave_length,
        )

        targets: list[WeeklyTarget] = []
        max_intensity = max(intensity_curve) if intensity_curve else start_weight
        for idx, (kpsh, intensity) in enumerate(zip(kpsh_curve, intensity_curve), start=1):
            if load_mode == "percent_1rm":
                pct = max(0.55, min(0.92, intensity / max(1.0, max_intensity)))
            else:
                pct = 0.0
            targets.append(
                WeeklyTarget(
                    week=idx,
                    kpsh=round(kpsh, 2),
                    intensity=round(intensity, 2),
                    tonnage=round(kpsh * intensity, 2),
                    intensity_pct_1rm=round(pct, 3),
                    phase="deload" if idx % max(2, wave_length) == 0 else "build",
                )
            )
        return targets
