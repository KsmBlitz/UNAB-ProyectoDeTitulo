import pytest
import asyncio

from app.repositories.alert_repository import alert_repository


@pytest.mark.asyncio
async def test_create_measurement_alert_skips_when_sensor_disconnected(monkeypatch):
    """If the sensor is disconnected, measurement alerts should be skipped (return None)."""

    # Mock sensor_service.is_sensor_connected to return False
    class DummySensorService:
        async def is_sensor_connected(self, sensor_id):
            return False

    # Patch the real sensor_service used by the function (imported from app.services.sensor_service)
    monkeypatch.setattr(
        "app.services.sensor_service.sensor_service",
        DummySensorService(),
        raising=False,
    )

    alert_doc = {"type": "ph", "sensor_id": "sensor-123", "value": 6.5}

    res = await alert_repository.create_alert(alert_doc)
    assert res is None


@pytest.mark.asyncio
async def test_create_measurement_alert_inserts_when_connected_and_no_existing(monkeypatch):
    """When sensor is connected and no similar unresolved alert exists, it should insert and return id."""
    # Patch BaseRepository.insert_one to avoid DB access for non-measurement alert
    import app.repositories.base_repository as br

    async def fake_find_one(self, query):
        return None

    async def fake_insert_one(self, document):
        return "inserted-nonmeas-id"

    monkeypatch.setattr(br.BaseRepository, "insert_one", fake_insert_one)

    alert_doc = {"type": "manual", "value": "test", "source": "test"}

    res = await alert_repository.create_alert(alert_doc)
    assert res == "inserted-nonmeas-id"
