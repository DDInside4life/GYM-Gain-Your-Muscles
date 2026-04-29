"""Periodization styles drive week-by-week intensity & volume waves.

Pure functions: given (style, week_index, total_weeks), return a multiplier
pair (intensity_mod, volume_mod) and a Russian descriptor for UI / params.
The generator multiplies the percent_1rm and the per-exercise sets count by
these values to shape an entire cycle.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class Periodization(str, Enum):
    dup = "dup"
    block = "block"
    linear = "linear"
    emergent = "emergent"


@dataclass(frozen=True, slots=True)
class WeekModifier:
    intensity: float
    volume: float
    label: str


_DEFAULT: Final[WeekModifier] = WeekModifier(1.0, 1.0, "")


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def week_modifier(
    style: Periodization | str | None,
    week_index: int,
    total_weeks: int,
) -> WeekModifier:
    """Return per-week intensity/volume scalers for the chosen style."""
    if total_weeks <= 0:
        return _DEFAULT
    style = _coerce(style)
    if style is None:
        return _DEFAULT
    if style == Periodization.linear:
        return _linear(week_index, total_weeks)
    if style == Periodization.block:
        return _block(week_index, total_weeks)
    if style == Periodization.dup:
        return _dup(week_index, total_weeks)
    if style == Periodization.emergent:
        return _emergent(week_index, total_weeks)
    return _DEFAULT


def _coerce(style: Periodization | str | None) -> Periodization | None:
    if style is None:
        return None
    if isinstance(style, Periodization):
        return style
    try:
        return Periodization(str(style).lower())
    except ValueError:
        return None


def _linear(week: int, total: int) -> WeekModifier:
    if total == 1:
        return WeekModifier(1.05, 1.0, "Линейная: пик")
    progress = (week - 1) / max(total - 1, 1)
    intensity = _clamp(0.92 + 0.16 * progress, 0.90, 1.08)
    volume = _clamp(1.10 - 0.30 * progress, 0.75, 1.10)
    return WeekModifier(intensity, volume, f"Линейная: неделя {week}/{total}")


def _block(week: int, total: int) -> WeekModifier:
    accumulation = max(1, round(total * 0.50))
    intensification = max(1, round(total * 0.30))
    deload_at = total
    if week <= accumulation:
        return WeekModifier(0.94, 1.10, f"Блок: накопление {week}/{accumulation}")
    if week <= accumulation + intensification:
        return WeekModifier(1.04, 0.95, "Блок: интенсификация")
    if week == deload_at:
        return WeekModifier(0.85, 0.65, "Блок: разгрузка")
    return WeekModifier(1.07, 0.80, "Блок: пик")


def _dup(week: int, total: int) -> WeekModifier:
    cycle = (week - 1) % 3
    if cycle == 0:
        return WeekModifier(1.05, 0.90, "DUP: тяжёлая волна")
    if cycle == 1:
        return WeekModifier(0.96, 1.05, "DUP: средняя волна")
    return WeekModifier(0.90, 1.10, "DUP: лёгкая волна")


def _emergent(week: int, total: int) -> WeekModifier:
    if week % 4 == 0:
        return WeekModifier(0.88, 0.75, "Эмерджентная: автоматическая разгрузка")
    base = 0.95 + (0.02 * ((week - 1) % 3))
    return WeekModifier(base, 1.0, f"Эмерджентная: авто-регуляция (неделя {week})")
