from fastapi import (
    FastAPI,
    status,
)
from fastapi.testclient import TestClient

import pytest
import pytest_asyncio
from faker import Faker
from httpx import Response
from presentation.api.auth import auth_service

from application.mediator import Mediator
from application.users.commands import CreateUserCommand
from domain.games.value_objects import GameStatus
from domain.users.entities import UserEntity


@pytest_asyncio.fixture
async def second_user(mediator: Mediator, faker: Faker) -> UserEntity:
    email = faker.email()
    password = faker.password(length=12)
    name = faker.name()

    result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email, password=password, name=name),
    )

    return result


@pytest.fixture
def second_authenticated_client(
    app: FastAPI,
    second_user: UserEntity,
) -> TestClient:
    client = TestClient(app=app)
    user_id = str(second_user.oid)
    access_token = auth_service.create_access_token(uid=user_id)
    refresh_token = auth_service.create_refresh_token(uid=user_id)

    client.cookies.set("access_token", access_token)
    client.cookies.set("refresh_token", refresh_token)

    return client


@pytest.mark.asyncio
async def test_create_game_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
):
    """Тест успешного создания игры."""
    url = app.url_path_for("create_game")

    response: Response = authenticated_client.post(url=url, json={})

    assert response.is_success
    assert response.status_code == status.HTTP_201_CREATED

    json_response = response.json()

    assert "data" in json_response
    game_data = json_response["data"]
    assert game_data["player_x_id"] == str(authenticated_user.oid)
    assert game_data["player_o_id"] is None
    assert game_data["status"] == GameStatus.WAITING
    assert game_data["current_turn"] == "X"
    assert game_data["winner_id"] is None
    assert game_data["finished_at"] is None
    assert "board" in game_data
    assert len(game_data["board"]) == 3
    assert all(len(row) == 3 for row in game_data["board"])


@pytest.mark.asyncio
async def test_create_game_unauthorized(
    app: FastAPI,
    client: TestClient,
):
    """Тест создания игры без аутентификации."""
    url = app.url_path_for("create_game")

    response: Response = client.post(url=url, json={})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_get_waiting_games_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
):
    """Тест получения списка ожидающих игр."""
    url = app.url_path_for("get_waiting_games")

    response: Response = authenticated_client.get(url=url)

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    assert "items" in json_response["data"]
    assert "pagination" in json_response["data"]
    assert isinstance(json_response["data"]["items"], list)


@pytest.mark.asyncio
async def test_get_waiting_games_with_created_game(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
):
    """Тест получения списка ожидающих игр после создания игры."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_data = create_response.json()["data"]

    url = app.url_path_for("get_waiting_games")
    response: Response = authenticated_client.get(url=url)

    assert response.is_success
    json_response = response.json()

    assert "data" in json_response
    items = json_response["data"]["items"]
    assert len(items) >= 1
    assert any(item["oid"] == game_data["oid"] for item in items)


@pytest.mark.asyncio
async def test_get_my_games_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
):
    """Тест получения списка моих игр."""
    url = app.url_path_for("get_my_games")

    response: Response = authenticated_client.get(url=url)

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    assert "items" in json_response["data"]
    assert isinstance(json_response["data"]["items"], list)


@pytest.mark.asyncio
async def test_get_my_games_with_created_game(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
):
    """Тест получения списка моих игр после создания игры."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_data = create_response.json()["data"]

    url = app.url_path_for("get_my_games")
    response: Response = authenticated_client.get(url=url)

    assert response.is_success
    json_response = response.json()

    assert "data" in json_response
    items = json_response["data"]["items"]
    assert len(items) >= 1
    assert any(item["oid"] == game_data["oid"] for item in items)


@pytest.mark.asyncio
async def test_get_my_games_unauthorized(
    app: FastAPI,
    client: TestClient,
):
    """Тест получения моих игр без аутентификации."""
    url = app.url_path_for("get_my_games")

    response: Response = client.get(url=url)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_get_game_by_id_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
):
    """Тест получения игры по ID."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    url = app.url_path_for("get_game", game_id=game_id)
    response: Response = authenticated_client.get(url=url)

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    game_data = json_response["data"]
    assert game_data["oid"] == game_id
    assert game_data["player_x_id"] == str(authenticated_user.oid)


@pytest.mark.asyncio
async def test_get_game_by_id_not_found(
    app: FastAPI,
    authenticated_client: TestClient,
    faker: Faker,
):
    """Тест получения несуществующей игры."""
    fake_game_id = faker.uuid4()

    url = app.url_path_for("get_game", game_id=fake_game_id)
    response: Response = authenticated_client.get(url=url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_join_game_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
    second_authenticated_client: TestClient,
    second_user: UserEntity,
):
    """Тест успешного присоединения к игре."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    response: Response = second_authenticated_client.post(url=join_url, json={})

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    game_data = json_response["data"]
    assert game_data["oid"] == game_id
    assert game_data["player_x_id"] == str(authenticated_user.oid)
    assert game_data["player_o_id"] == str(second_user.oid)
    assert game_data["status"] == GameStatus.ACTIVE


@pytest.mark.asyncio
async def test_join_game_unauthorized(
    app: FastAPI,
    authenticated_client: TestClient,
):
    """Тест присоединения к игре без аутентификации."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    unauth_client = TestClient(app=app)
    join_url = app.url_path_for("join_game", game_id=game_id)
    response: Response = unauth_client.post(url=join_url, json={})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_join_game_already_full(
    app: FastAPI,
    authenticated_client: TestClient,
    second_authenticated_client: TestClient,
    mediator: Mediator,
    faker: Faker,
):
    """Тест присоединения к уже заполненной игре."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    join_response: Response = second_authenticated_client.post(url=join_url, json={})
    assert join_response.is_success

    third_user_result, *_ = await mediator.handle_command(
        CreateUserCommand(
            email=faker.email(),
            password=faker.password(length=12),
            name=faker.name(),
        ),
    )
    third_user_id = str(third_user_result.oid)
    access_token = auth_service.create_access_token(uid=third_user_id)
    refresh_token = auth_service.create_refresh_token(uid=third_user_id)
    third_client = TestClient(app=app)
    third_client.cookies.set("access_token", access_token)
    third_client.cookies.set("refresh_token", refresh_token)

    response: Response = third_client.post(url=join_url, json={})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_make_move_success(
    app: FastAPI,
    authenticated_client: TestClient,
    second_authenticated_client: TestClient,
):
    """Тест успешного выполнения хода."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    join_response: Response = second_authenticated_client.post(url=join_url, json={})
    assert join_response.is_success

    move_url = app.url_path_for("make_move", game_id=game_id)
    response: Response = authenticated_client.post(
        url=move_url,
        json={"row": 0, "col": 0},
    )

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    game_data = json_response["data"]
    assert game_data["board"][0][0] == "X"
    assert game_data["current_turn"] == "O"


@pytest.mark.asyncio
async def test_make_move_unauthorized(
    app: FastAPI,
    authenticated_client: TestClient,
    second_authenticated_client: TestClient,
):
    """Тест выполнения хода без аутентификации."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    join_response: Response = second_authenticated_client.post(url=join_url, json={})
    assert join_response.is_success

    unauth_client = TestClient(app=app)
    move_url = app.url_path_for("make_move", game_id=game_id)
    response: Response = unauth_client.post(
        url=move_url,
        json={"row": 0, "col": 0},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_make_move_game_not_full(
    app: FastAPI,
    authenticated_client: TestClient,
):
    """Тест выполнения хода в игре, которая еще не заполнена."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    move_url = app.url_path_for("make_move", game_id=game_id)
    response: Response = authenticated_client.post(
        url=move_url,
        json={"row": 0, "col": 0},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_get_game_moves_success(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
    second_authenticated_client: TestClient,
):
    """Тест получения истории ходов игры."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    join_response: Response = second_authenticated_client.post(url=join_url, json={})
    assert join_response.is_success

    move_url = app.url_path_for("make_move", game_id=game_id)
    move_response: Response = authenticated_client.post(
        url=move_url,
        json={"row": 0, "col": 0},
    )
    assert move_response.is_success

    moves_url = app.url_path_for("get_game_moves", game_id=game_id)
    response: Response = authenticated_client.get(url=moves_url)

    assert response.is_success
    assert response.status_code == status.HTTP_200_OK

    json_response = response.json()

    assert "data" in json_response
    moves = json_response["data"]
    assert isinstance(moves, list)
    assert len(moves) == 1
    assert moves[0]["row"] == 0
    assert moves[0]["col"] == 0
    assert moves[0]["symbol"] == "X"
    assert moves[0]["player_id"] == str(authenticated_user.oid)


@pytest.mark.asyncio
async def test_get_game_moves_not_found(
    app: FastAPI,
    authenticated_client: TestClient,
    faker: Faker,
):
    """Тест получения ходов несуществующей игры."""
    fake_game_id = faker.uuid4()

    moves_url = app.url_path_for("get_game_moves", game_id=fake_game_id)
    response: Response = authenticated_client.get(url=moves_url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    json_response = response.json()
    assert "errors" in json_response


@pytest.mark.asyncio
async def test_full_game_win_x(
    app: FastAPI,
    authenticated_client: TestClient,
    authenticated_user: UserEntity,
    second_authenticated_client: TestClient,
):
    """Тест полноценной игры с победой X."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    join_response: Response = second_authenticated_client.post(url=join_url, json={})
    assert join_response.is_success

    move_url = app.url_path_for("make_move", game_id=game_id)

    moves = [
        (0, 0, authenticated_client),
        (1, 0, second_authenticated_client),
        (0, 1, authenticated_client),
        (1, 1, second_authenticated_client),
        (0, 2, authenticated_client),
    ]

    for row, col, client in moves:
        response: Response = client.post(
            url=move_url,
            json={"row": row, "col": col},
        )
        assert response.is_success

    final_response: Response = authenticated_client.get(
        url=app.url_path_for("get_game", game_id=game_id),
    )
    assert final_response.is_success

    game_data = final_response.json()["data"]

    assert game_data["status"] == GameStatus.FINISHED
    assert game_data["winner_id"] == str(authenticated_user.oid)
    assert game_data["finished_at"] is not None

    board = game_data["board"]
    assert board[0][0] == "X"
    assert board[0][1] == "X"
    assert board[0][2] == "X"

    moves_response: Response = authenticated_client.get(
        url=app.url_path_for("get_game_moves", game_id=game_id),
    )
    assert moves_response.is_success
    moves_data = moves_response.json()["data"]
    assert len(moves_data) == 5


@pytest.mark.asyncio
async def test_full_game_draw(
    app: FastAPI,
    authenticated_client: TestClient,
    second_authenticated_client: TestClient,
):
    """Тест полноценной игры с ничьей."""
    create_url = app.url_path_for("create_game")
    create_response: Response = authenticated_client.post(url=create_url, json={})
    assert create_response.is_success
    game_id = create_response.json()["data"]["oid"]

    join_url = app.url_path_for("join_game", game_id=game_id)
    join_response: Response = second_authenticated_client.post(url=join_url, json={})
    assert join_response.is_success

    move_url = app.url_path_for("make_move", game_id=game_id)

    moves = [
        (0, 0, authenticated_client),
        (0, 1, second_authenticated_client),
        (0, 2, authenticated_client),
        (1, 1, second_authenticated_client),
        (1, 0, authenticated_client),
        (1, 2, second_authenticated_client),
        (2, 1, authenticated_client),
        (2, 0, second_authenticated_client),
        (2, 2, authenticated_client),
    ]

    for row, col, client in moves:
        response: Response = client.post(
            url=move_url,
            json={"row": row, "col": col},
        )
        assert response.is_success

    final_response: Response = authenticated_client.get(
        url=app.url_path_for("get_game", game_id=game_id),
    )
    assert final_response.is_success

    game_data = final_response.json()["data"]

    assert game_data["status"] == GameStatus.FINISHED
    assert game_data["winner_id"] is None
    assert game_data["finished_at"] is not None

    moves_response: Response = authenticated_client.get(
        url=app.url_path_for("get_game_moves", game_id=game_id),
    )
    assert moves_response.is_success
    moves_data = moves_response.json()["data"]
    assert len(moves_data) == 9
