"""Unit tests for swap_dictionary.py."""
import pytest

from app.services.workout.swap_dictionary import suggest_swaps, SWAPS, _canonical_injury


@pytest.mark.parametrize("injury,canonical", [
    ("knee", "knee"),
    ("колено", "knee"),
    ("коленях", "knee"),
    ("back", "back"),
    ("поясница", "back"),
    ("плечо", "shoulder"),
    ("shoulder", "shoulder"),
    ("elbow", "elbow"),
    ("локоть", "elbow"),
    ("varicose", "varicose"),
    ("варикоз", "varicose"),
    ("hypertension", "hypertension"),
    ("гипертония", "hypertension"),
])
def test_canonical_injury_recognized(injury: str, canonical: str):
    assert _canonical_injury(injury) == canonical


def test_suggest_swaps_squat_knee():
    swaps = suggest_swaps("squat", ["knee"])
    assert "leg_press" in swaps
    assert "goblet_squat" in swaps


def test_suggest_swaps_deadlift_back():
    swaps = suggest_swaps("deadlift", ["back"])
    assert "hip_thrust" in swaps


def test_suggest_swaps_overhead_press_shoulder():
    swaps = suggest_swaps("overhead_press", ["shoulder"])
    assert "lateral_raise" in swaps


def test_suggest_swaps_overhead_press_hypertension():
    swaps = suggest_swaps("overhead_press", ["hypertension"])
    assert len(swaps) > 0


def test_suggest_swaps_no_injury():
    swaps = suggest_swaps("squat", [])
    assert swaps == []


def test_suggest_swaps_unknown_archetype():
    swaps = suggest_swaps("unknown_machine", ["knee"])
    assert isinstance(swaps, list)


def test_suggest_swaps_deduplicates():
    swaps = suggest_swaps("overhead_press", ["shoulder", "hypertension"])
    assert len(swaps) == len(set(swaps))
