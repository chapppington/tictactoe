from fastapi import (
    FastAPI,
    status,
)
from fastapi.testclient import TestClient

import pytest
from httpx import Response


@pytest.mark.asyncio
async def test_get_current_user_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user,
):
    """Тест успешного получения информации о текущем пользователе."""
    url = app.url_path_for("get_current_user")

    response: Response = authenticated_client.get(url=url)

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    assert json_response["data"]["oid"] == str(authenticated_user.oid)
    assert json_response["data"]["email"] == authenticated_user.email.as_generic_type()
    assert json_response["data"]["name"] == authenticated_user.name.as_generic_type()


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(
    app: FastAPI,
    client: TestClient,
):
    """Тест получения информации о пользователе без аутентификации."""
    url = app.url_path_for("get_current_user")

    response: Response = client.get(url=url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert "errors" in json_response
    assert len(json_response["errors"]) > 0
