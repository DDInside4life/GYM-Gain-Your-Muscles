from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.core.exceptions import Conflict
from app.services.idempotency import IdempotencyService


@dataclass
class _StoredRecord:
    request_hash: str
    response_status: int
    response_body: dict


class _FakeRepo:
    def __init__(self) -> None:
        self.items: dict[tuple[int, str, str], _StoredRecord] = {}

    async def get_by_scope(self, *, user_id: int, operation: str, idempotency_key: str):
        return self.items.get((user_id, operation, idempotency_key))

    async def add(self, record) -> None:
        self.items[(record.user_id, record.operation, record.idempotency_key)] = _StoredRecord(
            request_hash=record.request_hash,
            response_status=record.response_status,
            response_body=record.response_body,
        )


@pytest.mark.asyncio
async def test_execute_replays_stored_response_for_same_key_and_payload() -> None:
    repo = _FakeRepo()
    service = IdempotencyService(repo)  # type: ignore[arg-type]
    calls = 0

    async def _action() -> tuple[int, dict]:
        nonlocal calls
        calls += 1
        return 201, {"ok": True, "calls": calls}

    first = await service.execute(
        user_id=7,
        operation="workouts.log_set",
        idempotency_key="abc-1",
        request_payload={"set_index": 0, "completed_reps": 8},
        action=_action,
    )
    second = await service.execute(
        user_id=7,
        operation="workouts.log_set",
        idempotency_key="abc-1",
        request_payload={"set_index": 0, "completed_reps": 8},
        action=_action,
    )

    assert calls == 1
    assert first.replayed is False
    assert second.replayed is True
    assert second.body == {"ok": True, "calls": 1}


@pytest.mark.asyncio
async def test_execute_raises_conflict_for_same_key_different_payload() -> None:
    repo = _FakeRepo()
    service = IdempotencyService(repo)  # type: ignore[arg-type]

    async def _action() -> tuple[int, dict]:
        return 200, {"status": "ok"}

    await service.execute(
        user_id=7,
        operation="workouts.finalize_test_week",
        idempotency_key="same-key",
        request_payload={"plan_id": 10},
        action=_action,
    )

    with pytest.raises(Conflict):
        await service.execute(
            user_id=7,
            operation="workouts.finalize_test_week",
            idempotency_key="same-key",
            request_payload={"plan_id": 11},
            action=_action,
        )
