from __future__ import annotations

from app.services.workout.rules import compliance_adjustment


def test_compliance_adjustment_applies_low_compliance_limits() -> None:
    adjustment = compliance_adjustment(0.5)
    assert adjustment.reason == "low_compliance"
    assert adjustment.sets_delta == -1
    assert adjustment.intensity_cap == 0.95


def test_compliance_adjustment_applies_strict_limits_for_very_low_compliance() -> None:
    adjustment = compliance_adjustment(0.2)
    assert adjustment.reason == "very_low_compliance"
    assert adjustment.sets_delta == -2
    assert adjustment.intensity_cap == 0.9
