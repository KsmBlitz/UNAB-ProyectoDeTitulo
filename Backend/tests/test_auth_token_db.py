import pytest
from app.services.auth import create_access_token, get_user_from_token
from app.config.settings import settings


@pytest.mark.asyncio
async def test_get_user_from_token_success(monkeypatch):
    # Create a valid token
    token = create_access_token({"sub": "dbuser@example.com"})

    async def fake_find_one(query):
        assert query == {"email": "dbuser@example.com"}
        return {"email": "dbuser@example.com", "role": "usuario"}

    # Patch users_collection.find_one used by get_user_from_token
    monkeypatch.setattr("app.config.users_collection.find_one", fake_find_one, raising=False)

    user = await get_user_from_token(token)
    assert user["email"] == "dbuser@example.com"


@pytest.mark.asyncio
async def test_get_user_from_token_invalid_token(monkeypatch):
    # Use an invalid token string
    bad_token = "this.is.not.a.token"

    with pytest.raises(Exception):
        await get_user_from_token(bad_token)
