from __future__ import annotations

import pytest

from app.services.atomic import AtomicService


class _FakeSession:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_atomic_service_commits_once_on_success() -> None:
    db = _FakeSession()
    service = AtomicService(db)  # type: ignore[arg-type]

    result = await service.run(lambda: _ok_action())

    assert result == "ok"
    assert db.commits == 1
    assert db.rollbacks == 0


@pytest.mark.asyncio
async def test_atomic_service_rolls_back_on_failure() -> None:
    db = _FakeSession()
    service = AtomicService(db)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="boom"):
        await service.run(lambda: _fail_action())

    assert db.commits == 0
    assert db.rollbacks == 1


async def _ok_action() -> str:
    return "ok"


async def _fail_action() -> str:
    raise RuntimeError("boom")
