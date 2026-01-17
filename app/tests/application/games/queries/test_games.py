from uuid import uuid4

import pytest
from faker import Faker

from application.games.commands import (
    CreateGameCommand,
    JoinGameCommand,
    MakeMoveCommand,
)
from application.games.queries import (
    GetGameByIdQuery,
    GetGameMovesQuery,
    GetUserGamesQuery,
    GetWaitingGamesQuery,
)
from application.mediator import Mediator
from application.users.commands import CreateUserCommand
from domain.games.entities import GameEntity
from domain.games.exceptions import GameNotFoundException
from domain.games.value_objects import (
    GameStatus,
    PlayerSymbol,
)


@pytest.mark.asyncio
async def test_get_game_by_id_success(
    mediator: Mediator,
    faker: Faker,
):
    email = faker.email()
    password = faker.password(length=12)

    user_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email, password=password, name=faker.name()),
    )
    user = user_result

    game_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user.oid),
    )
    created_game: GameEntity = game_result

    retrieved_game = await mediator.handle_query(
        GetGameByIdQuery(game_id=created_game.oid),
    )

    assert retrieved_game.oid == created_game.oid
    assert retrieved_game.player_x_id == user.oid
    assert retrieved_game.status == GameStatus.WAITING


@pytest.mark.asyncio
async def test_get_game_by_id_not_found(
    mediator: Mediator,
):
    non_existent_id = uuid4()

    with pytest.raises(GameNotFoundException) as exc_info:
        await mediator.handle_query(
            GetGameByIdQuery(game_id=non_existent_id),
        )

    assert exc_info.value.game_id == non_existent_id


@pytest.mark.asyncio
async def test_get_waiting_games_query(
    mediator: Mediator,
    faker: Faker,
):
    email1 = faker.email()
    email2 = faker.email()
    password = faker.password(length=12)

    user1_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email1, password=password, name=faker.name()),
    )
    user1 = user1_result

    user2_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email2, password=password, name=faker.name()),
    )
    user2 = user2_result

    await mediator.handle_command(
        CreateGameCommand(player_x_id=user1.oid),
    )
    await mediator.handle_command(
        CreateGameCommand(player_x_id=user2.oid),
    )

    waiting_games = await mediator.handle_query(
        GetWaitingGamesQuery(limit=10, offset=0),
    )

    assert len(waiting_games) >= 2
    assert all(game.status == GameStatus.WAITING for game in waiting_games)


@pytest.mark.asyncio
async def test_get_waiting_games_query_empty(
    mediator: Mediator,
):
    waiting_games = await mediator.handle_query(
        GetWaitingGamesQuery(limit=10, offset=0),
    )

    assert isinstance(waiting_games, list)
    assert len(waiting_games) == 0


@pytest.mark.asyncio
async def test_get_user_games_query(
    mediator: Mediator,
    faker: Faker,
):
    email1 = faker.email()
    email2 = faker.email()
    password = faker.password(length=12)

    user1_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email1, password=password, name=faker.name()),
    )
    user1 = user1_result

    user2_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email2, password=password, name=faker.name()),
    )
    user2 = user2_result

    game1_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user1.oid),
    )
    game1 = game1_result

    game2_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user2.oid),
    )
    game2 = game2_result

    await mediator.handle_command(
        JoinGameCommand(game_id=game1.oid, player_o_id=user2.oid),
    )

    user1_games, user1_total = await mediator.handle_query(
        GetUserGamesQuery(user_id=user1.oid),
    )

    assert len(user1_games) >= 1
    assert user1_total >= 1
    assert any(game.oid == game1.oid for game in user1_games)

    user2_games, user2_total = await mediator.handle_query(
        GetUserGamesQuery(user_id=user2.oid),
    )

    assert len(user2_games) >= 2
    assert user2_total >= 2
    assert any(game.oid == game1.oid for game in user2_games)
    assert any(game.oid == game2.oid for game in user2_games)


@pytest.mark.asyncio
async def test_get_user_games_query_with_status_filter(
    mediator: Mediator,
    faker: Faker,
):
    email1 = faker.email()
    email2 = faker.email()
    password = faker.password(length=12)

    user1_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email1, password=password, name=faker.name()),
    )
    user1 = user1_result

    user2_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email2, password=password, name=faker.name()),
    )
    user2 = user2_result

    game_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user1.oid),
    )
    game = game_result

    await mediator.handle_command(
        JoinGameCommand(game_id=game.oid, player_o_id=user2.oid),
    )

    waiting_games, waiting_total = await mediator.handle_query(
        GetUserGamesQuery(user_id=user1.oid, status=GameStatus.WAITING),
    )

    assert len(waiting_games) == 0
    assert waiting_total == 0

    active_games, active_total = await mediator.handle_query(
        GetUserGamesQuery(user_id=user1.oid, status=GameStatus.ACTIVE),
    )

    assert len(active_games) >= 1
    assert active_total >= 1
    assert any(g.oid == game.oid for g in active_games)


@pytest.mark.asyncio
async def test_get_game_moves_query(
    mediator: Mediator,
    faker: Faker,
):
    email1 = faker.email()
    email2 = faker.email()
    password = faker.password(length=12)

    user1_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email1, password=password, name=faker.name()),
    )
    user1 = user1_result

    user2_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email2, password=password, name=faker.name()),
    )
    user2 = user2_result

    game_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user1.oid),
    )
    game = game_result

    await mediator.handle_command(
        JoinGameCommand(game_id=game.oid, player_o_id=user2.oid),
    )

    await mediator.handle_command(
        MakeMoveCommand(game_id=game.oid, player_id=user1.oid, row=0, col=0),
    )
    await mediator.handle_command(
        MakeMoveCommand(game_id=game.oid, player_id=user2.oid, row=1, col=1),
    )

    moves = await mediator.handle_query(
        GetGameMovesQuery(game_id=game.oid),
    )

    assert len(moves) == 2
    assert moves[0].row == 0
    assert moves[0].col == 0
    assert moves[0].symbol == PlayerSymbol.X
    assert moves[0].move_number == 1
    assert moves[1].row == 1
    assert moves[1].col == 1
    assert moves[1].symbol == PlayerSymbol.O
    assert moves[1].move_number == 2


@pytest.mark.asyncio
async def test_get_game_moves_query_empty(
    mediator: Mediator,
    faker: Faker,
):
    email = faker.email()
    password = faker.password(length=12)

    user_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email, password=password, name=faker.name()),
    )
    user = user_result

    game_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user.oid),
    )
    game = game_result

    moves = await mediator.handle_query(
        GetGameMovesQuery(game_id=game.oid),
    )

    assert isinstance(moves, list)
    assert len(moves) == 0


@pytest.mark.asyncio
async def test_get_game_moves_query_game_not_found(
    mediator: Mediator,
):
    non_existent_id = uuid4()

    with pytest.raises(GameNotFoundException) as exc_info:
        await mediator.handle_query(
            GetGameMovesQuery(game_id=non_existent_id),
        )

    assert exc_info.value.game_id == non_existent_id
