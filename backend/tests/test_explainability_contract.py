from __future__ import annotations

from app.schemas.workout import build_workout_explainability


def test_explainability_contains_percent_and_e1rm_base() -> None:
    explainability = build_workout_explainability(
        is_test_set=False,
        weight_kg=80.0,
        target_percent_1rm=0.8,
    )
    assert explainability is not None
    assert explainability.target_percent_1rm == 0.8
    assert explainability.based_on_e1rm == 100.0
    assert "estimated 1RM" in explainability.reason


def test_explainability_for_test_set_has_specific_reason() -> None:
    explainability = build_workout_explainability(
        is_test_set=True,
        weight_kg=60.0,
        target_percent_1rm=0.6,
    )
    assert explainability is not None
    assert "test-week" in explainability.reason
