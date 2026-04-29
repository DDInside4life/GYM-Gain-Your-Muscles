from __future__ import annotations

from app.core.error_handling import build_error_payload
from app.schemas.workout import build_workout_explainability


def test_error_contract_has_required_shape() -> None:
    payload = build_error_payload(
        error_code="invalid_request",
        message="Request validation failed",
        context={"field": "days_per_week"},
    )
    body = payload.model_dump()
    assert set(body.keys()) == {"error_code", "message", "context"}
    assert body["error_code"] == "invalid_request"
    assert body["message"] == "Request validation failed"


def test_workout_explainability_contract_shape() -> None:
    payload = build_workout_explainability(
        is_test_set=False,
        weight_kg=72.0,
        target_percent_1rm=0.8,
    )
    assert payload is not None
    body = payload.model_dump()
    assert set(body.keys()) == {"reason", "target_percent_1rm", "based_on_e1rm"}
    assert body["based_on_e1rm"] == 90.0
