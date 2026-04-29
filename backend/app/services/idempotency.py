from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Awaitable, Callable

from app.core.exceptions import Conflict
from app.models.idempotency import IdempotencyRecord
from app.repositories.idempotency import IdempotencyRepository


@dataclass(slots=True, frozen=True)
class IdempotentResponse:
    status_code: int
    body: dict
    replayed: bool


class IdempotencyService:
    def __init__(self, repo: IdempotencyRepository) -> None:
        self.repo = repo

    @staticmethod
    def request_hash(payload: dict) -> str:
        normalized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def execute(
        self,
        *,
        user_id: int,
        operation: str,
        idempotency_key: str | None,
        request_payload: dict,
        action: Callable[[], Awaitable[tuple[int, dict]]],
    ) -> IdempotentResponse:
        if not idempotency_key:
            status_code, body = await action()
            return IdempotentResponse(status_code=status_code, body=body, replayed=False)

        request_hash = self.request_hash(request_payload)
        existing = await self.repo.get_by_scope(
            user_id=user_id,
            operation=operation,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            if existing.request_hash != request_hash:
                raise Conflict(
                    "Idempotency key is already used with a different request payload",
                    error_code="idempotency_key_reused",
                    context={"operation": operation},
                )
            return IdempotentResponse(
                status_code=existing.response_status,
                body=dict(existing.response_body or {}),
                replayed=True,
            )

        status_code, body = await action()
        await self.repo.add(IdempotencyRecord(
            user_id=user_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status=status_code,
            response_body=body,
        ))
        return IdempotentResponse(status_code=status_code, body=body, replayed=False)
