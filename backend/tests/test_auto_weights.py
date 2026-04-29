"""Unit tests for auto_weights.py — pure math, no DB."""
import pytest

from app.services.workout.auto_weights import (
    AutoWeightCalculator,
    adjusted_e1rm,
    _rir_to_rpe_text,
)


def test_adjusted_e1rm_no_rir():
    result = adjusted_e1rm(100.0, 10, 0.0)
    assert result == pytest.approx(100 * (1 + 10 / 30), rel=1e-4)


def test_adjusted_e1rm_with_rir():
    result = adjusted_e1rm(80.0, 8, 2.0)
    assert result == pytest.approx(80 * (1 + 10 / 30), rel=1e-4)


def test_adjusted_e1rm_clamps_rir_below_zero():
    result = adjusted_e1rm(100.0, 10, -1.0)
    no_rir = adjusted_e1rm(100.0, 10, 0.0)
    assert result == no_rir


def test_adjusted_e1rm_clamps_rir_above_max():
    result = adjusted_e1rm(100.0, 10, 99.0)
    capped = adjusted_e1rm(100.0, 10, 5.0)
    assert result == capped


def test_rir_text_rir_one():
    text = _rir_to_rpe_text(1.0)
    assert "RIR 1" in text


def test_rir_text_rir_two():
    text = _rir_to_rpe_text(2.0)
    assert "RIR 2" in text


def test_rir_text_rir_three():
    text = _rir_to_rpe_text(3.0)
    assert "2" in text
