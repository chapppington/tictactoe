from uuid import uuid4

import pytest
from faker import Faker

from application.games.commands import (
    CreateGameCommand,
    JoinGameCommand,
    MakeMoveCommand,
)
from application.games.queries import GetGameByIdQuery
from application.mediator import Mediator
from application.users.commands import CreateUserCommand
from domain.games.entities import GameEntity
from domain.games.exceptions import (
    GameAlreadyFinishedException,
    GameAlreadyFullException,
    GameNotFoundException,
    InvalidMoveException,
    NotPlayerTurnException,
)
from domain.games.value_objects import (
    GameStatus,
    PlayerSymbol,
)


@pytest.mark.asyncio
async def test_create_game_command_success(
    mediator: Mediator,
    faker: Faker,
):
    email = faker.email()
    password = faker.password(length=12)
    name = faker.name()

    user_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email, password=password, name=name),
    )
    user = user_result

    result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user.oid),
    )

    game: GameEntity = result

    assert game is not None
    assert game.player_x_id == user.oid
    assert game.player_o_id is None
    assert game.status == GameStatus.WAITING
    assert game.current_turn == PlayerSymbol.X
    assert game.oid is not None

    retrieved_game = await mediator.handle_query(
        GetGameByIdQuery(game_id=game.oid),
    )

    assert retrieved_game.oid == game.oid
    assert retrieved_game.player_x_id == user.oid


@pytest.mark.asyncio
async def test_join_game_command_success(
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

    join_result, *_ = await mediator.handle_command(
        JoinGameCommand(game_id=game.oid, player_o_id=user2.oid),
    )

    joined_game: GameEntity = join_result

    assert joined_game.player_o_id == user2.oid
    assert joined_game.status == GameStatus.ACTIVE
    assert joined_game.is_full()


@pytest.mark.asyncio
async def test_join_game_command_game_not_found(
    mediator: Mediator,
    faker: Faker,
):
    email = faker.email()
    password = faker.password(length=12)

    user_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email, password=password, name=faker.name()),
    )
    user = user_result

    non_existent_game_id = uuid4()

    with pytest.raises(GameNotFoundException) as exc_info:
        await mediator.handle_command(
            JoinGameCommand(game_id=non_existent_game_id, player_o_id=user.oid),
        )

    assert exc_info.value.game_id == non_existent_game_id


@pytest.mark.asyncio
async def test_join_game_command_already_full(
    mediator: Mediator,
    faker: Faker,
):
    email1 = faker.email()
    email2 = faker.email()
    email3 = faker.email()
    password = faker.password(length=12)

    user1_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email1, password=password, name=faker.name()),
    )
    user1 = user1_result

    user2_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email2, password=password, name=faker.name()),
    )
    user2 = user2_result

    user3_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email3, password=password, name=faker.name()),
    )
    user3 = user3_result

    game_result, *_ = await mediator.handle_command(
        CreateGameCommand(player_x_id=user1.oid),
    )
    game = game_result

    await mediator.handle_command(
        JoinGameCommand(game_id=game.oid, player_o_id=user2.oid),
    )

    with pytest.raises(GameAlreadyFullException) as exc_info:
        await mediator.handle_command(
            JoinGameCommand(game_id=game.oid, player_o_id=user3.oid),
        )

    assert exc_info.value.game_id == game.oid


@pytest.mark.asyncio
async def test_join_game_command_already_finished(
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

    game.status = GameStatus.FINISHED

    with pytest.raises(GameAlreadyFinishedException) as exc_info:
        await mediator.handle_command(
            JoinGameCommand(game_id=game.oid, player_o_id=user2.oid),
        )

    assert exc_info.value.game_id == game.oid


@pytest.mark.asyncio
async def test_make_move_command_success(
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

    move_result, *_ = await mediator.handle_command(
        MakeMoveCommand(game_id=game.oid, player_id=user1.oid, row=0, col=0),
    )

    moved_game: GameEntity = move_result

    assert moved_game.board[0][0] == PlayerSymbol.X
    assert moved_game.current_turn == PlayerSymbol.O


@pytest.mark.asyncio
async def test_make_move_command_game_not_found(
    mediator: Mediator,
    faker: Faker,
):
    email = faker.email()
    password = faker.password(length=12)

    user_result, *_ = await mediator.handle_command(
        CreateUserCommand(email=email, password=password, name=faker.name()),
    )
    user = user_result

    non_existent_game_id = uuid4()

    with pytest.raises(GameNotFoundException) as exc_info:
        await mediator.handle_command(
            MakeMoveCommand(
                game_id=non_existent_game_id,
                player_id=user.oid,
                row=0,
                col=0,
            ),
        )

    assert exc_info.value.game_id == non_existent_game_id


@pytest.mark.asyncio
async def test_make_move_command_not_player_turn(
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

    with pytest.raises(NotPlayerTurnException) as exc_info:
        await mediator.handle_command(
            MakeMoveCommand(game_id=game.oid, player_id=user2.oid, row=0, col=0),
        )

    assert exc_info.value.game_id == game.oid
    assert exc_info.value.player_id == user2.oid


@pytest.mark.asyncio
async def test_make_move_command_invalid_position(
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

    with pytest.raises(InvalidMoveException) as exc_info:
        await mediator.handle_command(
            MakeMoveCommand(game_id=game.oid, player_id=user2.oid, row=0, col=0),
        )

    assert exc_info.value.game_id == game.oid


@pytest.mark.asyncio
async def test_make_move_command_game_not_full(
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

    with pytest.raises(InvalidMoveException) as exc_info:
        await mediator.handle_command(
            MakeMoveCommand(game_id=game.oid, player_id=user.oid, row=0, col=0),
        )

    assert exc_info.value.game_id == game.oid
    assert "not full" in exc_info.value.reason.lower()


@pytest.mark.asyncio
async def test_make_move_command_win_game(
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
        MakeMoveCommand(game_id=game.oid, player_id=user2.oid, row=1, col=0),
    )
    await mediator.handle_command(
        MakeMoveCommand(game_id=game.oid, player_id=user1.oid, row=0, col=1),
    )
    await mediator.handle_command(
        MakeMoveCommand(game_id=game.oid, player_id=user2.oid, row=1, col=1),
    )

    win_result, *_ = await mediator.handle_command(
        MakeMoveCommand(game_id=game.oid, player_id=user1.oid, row=0, col=2),
    )

    finished_game: GameEntity = win_result

    assert finished_game.status == GameStatus.FINISHED
    assert finished_game.winner_id == user1.oid
    assert finished_game.finished_at is not None
