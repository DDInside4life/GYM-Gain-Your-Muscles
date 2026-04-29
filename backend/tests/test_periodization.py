from __future__ import annotations

from app.services.workout.periodization import (
    Periodization,
    week_modifier,
)


def test_unknown_style_returns_neutral_modifier():
    mod = week_modifier(None, 1, 4)
    assert mod.intensity == 1.0
    assert mod.volume == 1.0


def test_linear_intensity_grows_volume_drops():
    first = week_modifier(Periodization.linear, 1, 6)
    last = week_modifier(Periodization.linear, 6, 6)
    assert last.intensity > first.intensity
    assert last.volume < first.volume


def test_block_has_deload_at_end():
    deload = week_modifier(Periodization.block, 6, 6)
    accumulation = week_modifier(Periodization.block, 1, 6)
    assert deload.intensity < accumulation.intensity
    assert deload.volume < 1.0


def test_dup_alternates_waves():
    heavy = week_modifier(Periodization.dup, 1, 6)
    medium = week_modifier(Periodization.dup, 2, 6)
    light = week_modifier(Periodization.dup, 3, 6)
    assert heavy.intensity > medium.intensity > light.intensity
    assert heavy.volume < medium.volume < light.volume


def test_emergent_inserts_periodic_deload():
    deload = week_modifier(Periodization.emergent, 4, 8)
    regular = week_modifier(Periodization.emergent, 5, 8)
    assert deload.volume < regular.volume
    assert deload.intensity < regular.intensity


def test_string_input_is_accepted():
    mod = week_modifier("dup", 1, 4)
    assert mod.label
