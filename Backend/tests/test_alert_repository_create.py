import asyncio
import pytest

from app.repositories.alert_repository import AlertRepository, alert_repository
import importlib
sensor_service_module = importlib.import_module("app.services.sensor_service")


@pytest.mark.asyncio
async def test_create_alert_skips_disconnected(monkeypatch):
    """create_alert should return None and not call insert when sensor disconnected"""
    repo = AlertRepository()

    # Sample alert doc for a measurement type
    alert_doc = {"type": "ph", "sensor_id": "sensor-123"}

    # Patch sensor_service.is_sensor_connected to return False
    async def fake_is_connected(_):
        return False

    # Patch the module-level singleton with a fake object that has the async method
    class FakeService:
        async def is_sensor_connected(self, _):
            return await fake_is_connected(_)

    monkeypatch.setattr(sensor_service_module, "sensor_service", FakeService())

    # Patch BaseRepository.insert_one to raise if called (should not be called)
    async def fail_insert(doc):
        raise AssertionError("insert_one should not be called for disconnected sensors")

    monkeypatch.setattr("app.repositories.base_repository.BaseRepository.insert_one", fail_insert)

    result = await repo.create_alert(alert_doc)
    assert result is None


@pytest.mark.asyncio
async def test_create_alert_inserts_when_connected(monkeypatch):
    """create_alert should call insert_one and return inserted id when sensor connected and no duplicate"""
    repo = AlertRepository()

    alert_doc = {"type": "ph", "sensor_id": "sensor-abc"}

    async def fake_is_connected(_):
        return True

    class FakeService2:
        async def is_sensor_connected(self, _):
            return await fake_is_connected(_)

    monkeypatch.setattr(sensor_service_module, "sensor_service", FakeService2())

    # Patch collection.find_one to return None (no duplicate)
    async def fake_find_one(query):
        return None

    monkeypatch.setattr(repo, "collection", type("C", (), {"find_one": staticmethod(fake_find_one)}))

    async def fake_insert_one(self, doc):
        # Simulate BaseRepository.insert_one returning a string id
        return "abc123"

    monkeypatch.setattr("app.repositories.base_repository.BaseRepository.insert_one", fake_insert_one)

    inserted = await repo.create_alert(alert_doc)
    assert inserted == "abc123"
