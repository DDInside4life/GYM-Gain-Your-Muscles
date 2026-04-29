from __future__ import annotations

from app.services.workout.generator import _apply_modifier, resolve_total_weeks
from app.services.workout.load_progression import Prescription
from app.services.workout.periodization import WeekModifier


def _prescription(**overrides) -> Prescription:
    base = dict(
        sets=4,
        reps_min=6,
        reps_max=10,
        rest_sec=120,
        weight_kg=80.0,
        target_percent_1rm=0.7,
        target_rir=2.0,
        rpe_text="",
        is_test_set=False,
        test_instruction="",
        notes="base",
    )
    base.update(overrides)
    return Prescription(**base)


def test_apply_modifier_neutral_returns_same():
    p = _prescription()
    out = _apply_modifier(p, WeekModifier(1.0, 1.0, ""))
    assert out is p


def test_apply_modifier_scales_intensity_and_volume():
    p = _prescription()
    out = _apply_modifier(p, WeekModifier(1.10, 0.75, "DUP: тяжёлая волна"))
    assert out.weight_kg == round(80.0 * 1.10, 1)
    assert out.target_percent_1rm == round(0.7 * 1.10, 4)
    assert out.sets == max(1, round(4 * 0.75))
    assert "DUP" in out.notes


def test_apply_modifier_clamps_sets():
    p = _prescription(sets=10)
    out = _apply_modifier(p, WeekModifier(1.0, 1.5, ""))
    assert out.sets <= 8
    out2 = _apply_modifier(_prescription(sets=1), WeekModifier(1.0, 0.1, ""))
    assert out2.sets >= 1


def test_apply_modifier_handles_none_weight():
    p = _prescription(weight_kg=None, target_percent_1rm=None)
    out = _apply_modifier(p, WeekModifier(1.1, 0.8, ""))
    assert out.weight_kg is None
    assert out.target_percent_1rm is None


def test_resolve_total_weeks_clamps_and_defaults():
    assert resolve_total_weeks(None) == 4
    assert resolve_total_weeks("8") == 8
    assert resolve_total_weeks(20) == 12
    assert resolve_total_weeks(0) == 3
