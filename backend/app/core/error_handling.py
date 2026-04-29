from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.schemas.error import ApiErrorResponse

logger = logging.getLogger("app")

_DEFAULT_MESSAGES: dict[str, str] = {
    "invalid_request": "Request validation failed",
    "resource_not_found": "Resource not found",
    "auth_unauthorized": "Authentication required",
    "access_forbidden": "Access denied",
    "state_conflict": "Request conflicts with current resource state",
    "rate_limited": "Too many requests",
    "internal_error": "Unexpected server error",
}


def _error_message(error_code: str, fallback: str | None) -> str:
    if fallback:
        return fallback
    return _DEFAULT_MESSAGES.get(error_code, "Request failed")


def build_error_payload(
    *,
    error_code: str,
    message: str | None = None,
    context: dict[str, Any] | None = None,
) -> ApiErrorResponse:
    return ApiErrorResponse(
        error_code=error_code,
        message=_error_message(error_code, message),
        context=context,
    )


def _json_error(status_code: int, payload: ApiErrorResponse) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        payload = build_error_payload(
            error_code=exc.error_code,
            message=str(exc.detail) if exc.detail else None,
            context=exc.context,
        )
        return _json_error(exc.status_code, payload)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = build_error_payload(
            error_code="invalid_request",
            context={"errors": exc.errors()},
        )
        return _json_error(422, payload)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            payload = build_error_payload(error_code="resource_not_found")
            return _json_error(404, payload)
        if exc.status_code == 429:
            payload = build_error_payload(error_code="rate_limited")
            return _json_error(429, payload)
        payload = build_error_payload(
            error_code=f"http_{exc.status_code}",
            message=str(exc.detail) if exc.detail else None,
        )
        return _json_error(exc.status_code, payload)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error: %s", exc)
        payload = build_error_payload(error_code="internal_error")
        return _json_error(500, payload)
