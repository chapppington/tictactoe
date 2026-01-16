from uuid import uuid4

from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.value_objects import (
    BoardPosition,
    GameStatus,
    PlayerSymbol,
)


def test_game_entity_creation():
    player_x_id = uuid4()

    game = GameEntity(player_x_id=player_x_id)

    assert game.player_x_id == player_x_id
    assert game.player_o_id is None
    assert game.status == GameStatus.WAITING
    assert game.current_turn == PlayerSymbol.X
    assert game.winner_id is None
    assert game.finished_at is None
    assert game.oid is not None
    assert game.created_at is not None
    assert game.updated_at is not None
    assert len(game.board) == 3
    assert all(len(row) == 3 for row in game.board)
    assert all(cell is None for row in game.board for cell in row)


def test_game_entity_is_full():
    player_x_id = uuid4()
    player_o_id = uuid4()

    game = GameEntity(player_x_id=player_x_id)
    assert not game.is_full()

    game.player_o_id = player_o_id
    assert game.is_full()


def test_game_entity_is_position_empty():
    player_x_id = uuid4()
    game = GameEntity(player_x_id=player_x_id)

    assert game.is_position_empty(0, 0)
    assert game.is_position_empty(1, 2)
    assert game.is_position_empty(2, 1)

    game.board[0][0] = PlayerSymbol.X
    assert not game.is_position_empty(0, 0)


def test_game_entity_make_move():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    position = BoardPosition(value=(1, 2))
    game.make_move(player_x_id, position)

    assert game.board[1][2] == PlayerSymbol.X
    assert game.current_turn == PlayerSymbol.O

    position2 = BoardPosition(value=(0, 0))
    game.make_move(player_o_id, position2)

    assert game.board[0][0] == PlayerSymbol.O
    assert game.current_turn == PlayerSymbol.X


def test_game_entity_make_move_on_occupied_position():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    position = BoardPosition(value=(1, 1))
    game.make_move(player_x_id, position)
    assert game.board[1][1] == PlayerSymbol.X

    game.make_move(player_o_id, position)
    assert game.board[1][1] == PlayerSymbol.X


def test_game_entity_check_winner_horizontal():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[0][0] = PlayerSymbol.X
    game.board[0][1] = PlayerSymbol.X
    game.board[0][2] = PlayerSymbol.X

    winner = game.check_winner()
    assert winner == PlayerSymbol.X


def test_game_entity_check_winner_vertical():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[0][1] = PlayerSymbol.O
    game.board[1][1] = PlayerSymbol.O
    game.board[2][1] = PlayerSymbol.O

    winner = game.check_winner()
    assert winner == PlayerSymbol.O


def test_game_entity_check_winner_diagonal_main():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[0][0] = PlayerSymbol.X
    game.board[1][1] = PlayerSymbol.X
    game.board[2][2] = PlayerSymbol.X

    winner = game.check_winner()
    assert winner == PlayerSymbol.X


def test_game_entity_check_winner_diagonal_anti():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[0][2] = PlayerSymbol.O
    game.board[1][1] = PlayerSymbol.O
    game.board[2][0] = PlayerSymbol.O

    winner = game.check_winner()
    assert winner == PlayerSymbol.O


def test_game_entity_check_winner_no_winner():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[0][0] = PlayerSymbol.X
    game.board[0][1] = PlayerSymbol.O
    game.board[0][2] = PlayerSymbol.X

    winner = game.check_winner()
    assert winner is None


def test_game_entity_is_board_full():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    assert not game.is_board_full()

    for i in range(3):
        for j in range(3):
            game.board[i][j] = PlayerSymbol.X if (i + j) % 2 == 0 else PlayerSymbol.O

    assert game.is_board_full()


def test_game_entity_get_winner_id_x():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[0][0] = PlayerSymbol.X
    game.board[0][1] = PlayerSymbol.X
    game.board[0][2] = PlayerSymbol.X

    winner_id = game.get_winner_id()
    assert winner_id == player_x_id


def test_game_entity_get_winner_id_o():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    game.board[1][0] = PlayerSymbol.O
    game.board[1][1] = PlayerSymbol.O
    game.board[1][2] = PlayerSymbol.O

    winner_id = game.get_winner_id()
    assert winner_id == player_o_id


def test_game_entity_get_winner_id_none():
    player_x_id = uuid4()
    player_o_id = uuid4()
    game = GameEntity(player_x_id=player_x_id, player_o_id=player_o_id, status=GameStatus.ACTIVE)

    winner_id = game.get_winner_id()
    assert winner_id is None


def test_game_entity_equality():
    game_id = uuid4()
    player_x_id = uuid4()

    game1 = GameEntity(oid=game_id, player_x_id=player_x_id)
    game2 = GameEntity(oid=game_id, player_x_id=player_x_id)

    assert game1 == game2


def test_game_entity_inequality():
    player_x_id = uuid4()

    game1 = GameEntity(player_x_id=player_x_id)
    game2 = GameEntity(player_x_id=player_x_id)

    assert game1 != game2


def test_game_move_creation():
    game_id = uuid4()
    player_id = uuid4()

    move = GameMove(
        game_id=game_id,
        player_id=player_id,
        row=1,
        col=2,
        symbol=PlayerSymbol.X,
        move_number=1,
    )

    assert move.game_id == game_id
    assert move.player_id == player_id
    assert move.row == 1
    assert move.col == 2
    assert move.symbol == PlayerSymbol.X
    assert move.move_number == 1
    assert move.oid is not None
    assert move.created_at is not None
    assert move.updated_at is not None


def test_game_move_equality():
    move_id = uuid4()
    game_id = uuid4()
    player_id = uuid4()

    move1 = GameMove(
        oid=move_id,
        game_id=game_id,
        player_id=player_id,
        row=1,
        col=2,
        symbol=PlayerSymbol.X,
        move_number=1,
    )
    move2 = GameMove(
        oid=move_id,
        game_id=game_id,
        player_id=player_id,
        row=0,
        col=0,
        symbol=PlayerSymbol.O,
        move_number=2,
    )

    assert move1 == move2


def test_game_move_inequality():
    game_id = uuid4()
    player_id = uuid4()

    move1 = GameMove(
        game_id=game_id,
        player_id=player_id,
        row=1,
        col=2,
        symbol=PlayerSymbol.X,
        move_number=1,
    )
    move2 = GameMove(
        game_id=game_id,
        player_id=player_id,
        row=1,
        col=2,
        symbol=PlayerSymbol.X,
        move_number=1,
    )

    assert move1 != move2
