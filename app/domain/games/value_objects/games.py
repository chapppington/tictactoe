from dataclasses import dataclass
from enum import Enum

from domain.base.value_object import BaseValueObject
from domain.games.exceptions import InvalidBoardPositionException


class GameStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class PlayerSymbol(str, Enum):
    X = "X"
    O = "O"  # noqa: E741


@dataclass(frozen=True)
class BoardPosition(BaseValueObject[tuple[int, int]]):
    value: tuple[int, int]

    def __post_init__(self):
        self.validate()

    @property
    def row(self) -> int:
        return self.value[0]

    @property
    def col(self) -> int:
        return self.value[1]

    def validate(self):
        row, col = self.value
        if not (0 <= row < 3):
            raise InvalidBoardPositionException(
                position=(row, col),
                reason=f"Row must be between 0 and 2, got {row}",
            )
        if not (0 <= col < 3):
            raise InvalidBoardPositionException(
                position=(row, col),
                reason=f"Column must be between 0 and 2, got {col}",
            )

    def as_generic_type(self) -> tuple[int, int]:
        return self.value
