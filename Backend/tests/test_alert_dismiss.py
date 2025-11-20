import pytest
import asyncio
from datetime import datetime, timezone

from app.repositories.alert_repository import alert_repository


@pytest.mark.asyncio
async def test_dismiss_alert_no_alert(monkeypatch):
    async def fake_find_by_id(self, id):
        return None

    monkeypatch.setattr("app.repositories.base_repository.BaseRepository.find_by_id", fake_find_by_id, raising=True)

    res = await alert_repository.dismiss_alert("nonexistent", "tester")
    assert res is False


@pytest.mark.asyncio
async def test_dismiss_alert_success_fallback_move(monkeypatch):
    # prepare a fake alert
    alert = {
        "_id": "alert-1",
        "type": "ph",
        "created_at": datetime.now(timezone.utc)
    }

    async def fake_find_by_id(self, id):
        return alert

    async def fake_update_one(self, query, update):
        return True

    moved = {"called": False}

    async def fake_move_to_history(self, alert_obj, dismissed_by, reason):
        moved["called"] = True

    # Force asyncio.create_task to raise so dismiss_alert falls back to synchronous move
    def raise_create_task(coro):
        raise RuntimeError("cannot schedule")

    monkeypatch.setattr("app.repositories.base_repository.BaseRepository.find_by_id", fake_find_by_id, raising=True)
    monkeypatch.setattr("app.repositories.base_repository.BaseRepository.update_one", fake_update_one, raising=True)
    monkeypatch.setattr("app.repositories.alert_repository.AlertRepository._move_to_history", fake_move_to_history, raising=True)
    monkeypatch.setattr("asyncio.create_task", raise_create_task, raising=False)

    res = await alert_repository.dismiss_alert("alert-1", "tester")
    assert res is True
    assert moved["called"] is True
