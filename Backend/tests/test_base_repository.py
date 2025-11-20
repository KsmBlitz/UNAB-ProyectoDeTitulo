import pytest

from app.repositories.base_repository import BaseRepository


class DummyCollection:
    def __init__(self):
        self._last = None

    async def insert_one(self, doc):
        class R:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        self._last = doc
        return R(inserted_id="oid-xyz")


def test_insert_one_returns_string_id(monkeypatch):
    # Create a BaseRepository with a dummy collection
    repo = BaseRepository(collection=None)
    dummy = DummyCollection()
    # monkeypatch repo.collection
    repo.collection = dummy

    # call insert_one (synchronous wrapper calls underlying async insert)
    # BaseRepository.insert_one is async; use pytest.mark.asyncio style by running loop
    import asyncio

    async def run():
        res = await repo.insert_one({"a": 1})
        return res

    loop = asyncio.get_event_loop()
    out = loop.run_until_complete(run())
    assert out == "oid-xyz"
