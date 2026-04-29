from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_handling import register_exception_handlers
from app.core.exceptions import BadRequest


def _client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/bad-request")
    async def bad_request() -> None:
        raise BadRequest(
            "Workout plan is required",
            error_code="workout_plan_required",
            context={"field": "plan_id"},
        )

    @app.get("/explode")
    async def explode() -> None:
        raise RuntimeError("boom")

    @app.get("/validate")
    async def validate(value: int) -> dict[str, int]:
        return {"value": value}

    return TestClient(app, raise_server_exceptions=False)


def test_business_error_payload_is_ui_friendly() -> None:
    response = _client().get("/bad-request")

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "workout_plan_required",
        "message": "Workout plan is required",
        "context": {"field": "plan_id"},
    }


def test_validation_error_is_mapped() -> None:
    response = _client().get("/validate", params={"value": "not-int"})

    assert response.status_code == 422
    body = response.json()
    assert body["error_code"] == "invalid_request"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["context"], dict)
    assert body["context"]["errors"]


def test_unhandled_error_is_mapped() -> None:
    response = _client().get("/explode")

    assert response.status_code == 500
    assert response.json() == {
        "error_code": "internal_error",
        "message": "Unexpected server error",
        "context": None,
    }
