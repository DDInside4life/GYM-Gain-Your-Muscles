from __future__ import annotations

from app.models.user import Experience
from app.services.workout.session_duration import (
    DEFAULT_DURATION_MIN,
    cap_for,
    normalize_duration,
    session_shape,
)


def test_normalize_duration_snaps_to_allowed():
    assert normalize_duration(40) == 45
    assert normalize_duration(75) == 60 or normalize_duration(75) == 90
    assert normalize_duration(None) == DEFAULT_DURATION_MIN


def test_session_shape_for_known_durations():
    short = session_shape(45)
    long = session_shape(150)
    assert short.max_exercises < long.max_exercises
    assert "45" in short.label or "Экспресс" in short.label


def test_cap_for_reduces_for_short_sessions():
    base_cap = 6
    short = cap_for(45, Experience.intermediate, base_cap)
    long = cap_for(120, Experience.intermediate, base_cap)
    assert short <= long
    assert short >= 4


def test_cap_for_never_below_minimum():
    assert cap_for(45, Experience.beginner, 3) >= 4
