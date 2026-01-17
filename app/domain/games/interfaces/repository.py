from abc import (
    ABC,
    abstractmethod,
)
from uuid import UUID

from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.value_objects import GameStatus


class BaseGameRepository(ABC):
    @abstractmethod
    async def add(self, game: GameEntity) -> None: ...

    @abstractmethod
    async def get_by_id(self, game_id: UUID) -> GameEntity | None: ...

    @abstractmethod
    async def update(self, game: GameEntity) -> None: ...

    @abstractmethod
    async def get_waiting_games(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]: ...

    @abstractmethod
    async def get_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]: ...

    @abstractmethod
    async def count_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
    ) -> int: ...


class BaseGameMoveRepository(ABC):
    @abstractmethod
    async def add(self, move: GameMove) -> None: ...

    @abstractmethod
    async def get_by_game_id(
        self,
        game_id: UUID,
    ) -> list[GameMove]: ...
