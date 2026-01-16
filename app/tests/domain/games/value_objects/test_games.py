import pytest

from domain.games.exceptions import InvalidBoardPositionException
from domain.games.value_objects import (
    BoardPosition,
    GameStatus,
    PlayerSymbol,
)


@pytest.mark.parametrize(
    "status_value",
    [
        GameStatus.WAITING,
        GameStatus.ACTIVE,
        GameStatus.FINISHED,
        GameStatus.CANCELLED,
    ],
)
def test_game_status_values(status_value):
    assert status_value in GameStatus


@pytest.mark.parametrize(
    "symbol_value",
    [
        PlayerSymbol.X,
        PlayerSymbol.O,
    ],
)
def test_player_symbol_values(symbol_value):
    assert symbol_value in PlayerSymbol


@pytest.mark.parametrize(
    "row,col,expected",
    [
        (0, 0, (0, 0)),
        (1, 2, (1, 2)),
        (2, 1, (2, 1)),
        (0, 2, (0, 2)),
    ],
)
def test_board_position_valid(row, col, expected):
    position = BoardPosition(value=(row, col))
    assert position.value == expected
    assert position.row == row
    assert position.col == col


@pytest.mark.parametrize(
    "row,col,exception",
    [
        (-1, 0, InvalidBoardPositionException),
        (0, -1, InvalidBoardPositionException),
        (3, 0, InvalidBoardPositionException),
        (0, 3, InvalidBoardPositionException),
        (5, 5, InvalidBoardPositionException),
    ],
)
def test_board_position_invalid(row, col, exception):
    with pytest.raises(exception):
        BoardPosition(value=(row, col))


def test_board_position_as_generic_type():
    position = BoardPosition(value=(1, 2))
    assert position.as_generic_type() == (1, 2)
