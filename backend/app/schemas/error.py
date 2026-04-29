from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiErrorResponse(BaseModel):
    error_code: str
    message: str
    context: dict[str, Any] | None = None
