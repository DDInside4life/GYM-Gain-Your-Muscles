from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(
        self,
        code: int,
        detail: str,
        *,
        error_code: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=code, detail=detail)
        self.error_code = error_code
        self.context = context


class NotFound(AppError):
    def __init__(
        self,
        detail: str = "Not found",
        *,
        error_code: str = "resource_not_found",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, detail, error_code=error_code, context=context)


class Unauthorized(AppError):
    def __init__(
        self,
        detail: str = "Unauthorized",
        *,
        error_code: str = "auth_unauthorized",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail, error_code=error_code, context=context)


class Forbidden(AppError):
    def __init__(
        self,
        detail: str = "Forbidden",
        *,
        error_code: str = "access_forbidden",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, detail, error_code=error_code, context=context)


class Conflict(AppError):
    def __init__(
        self,
        detail: str = "Conflict",
        *,
        error_code: str = "state_conflict",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status.HTTP_409_CONFLICT, detail, error_code=error_code, context=context)


class BadRequest(AppError):
    def __init__(
        self,
        detail: str = "Bad request",
        *,
        error_code: str = "invalid_request",
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status.HTTP_400_BAD_REQUEST, detail, error_code=error_code, context=context)
