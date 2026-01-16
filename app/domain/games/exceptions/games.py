from dataclasses import dataclass
from uuid import UUID

from domain.base.exceptions import DomainException


@dataclass(eq=False)
class GameException(DomainException):
    @property
    def message(self) -> str:
        return "Game exception occurred"


@dataclass(eq=False)
class GameNotFoundException(GameException):
    game_id: UUID

    @property
    def message(self) -> str:
        return f"Game with id {self.game_id} not found"


@dataclass(eq=False)
class GameAlreadyFinishedException(GameException):
    game_id: UUID

    @property
    def message(self) -> str:
        return f"Game with id {self.game_id} is already finished"


@dataclass(eq=False)
class GameAlreadyFullException(GameException):
    game_id: UUID

    @property
    def message(self) -> str:
        return f"Game with id {self.game_id} is already full"


@dataclass(eq=False)
class InvalidMoveException(GameException):
    game_id: UUID
    reason: str

    @property
    def message(self) -> str:
        return f"Invalid move in game {self.game_id}: {self.reason}"


@dataclass(eq=False)
class NotPlayerTurnException(GameException):
    game_id: UUID
    player_id: UUID

    @property
    def message(self) -> str:
        return f"It is not player {self.player_id}'s turn in game {self.game_id}"


@dataclass(eq=False)
class InvalidBoardPositionException(GameException):
    position: tuple[int, int]
    reason: str

    @property
    def message(self) -> str:
        return f"Invalid board position {self.position}: {self.reason}"


@dataclass(eq=False)
class InvalidPlayerSymbolException(GameException):
    symbol: str

    @property
    def message(self) -> str:
        return f"Invalid player symbol: {self.symbol}. Must be 'X' or 'O'"
