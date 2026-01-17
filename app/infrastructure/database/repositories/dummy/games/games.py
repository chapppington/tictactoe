from dataclasses import (
    dataclass,
    field,
)
from uuid import UUID

from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.interfaces.repository import (
    BaseGameMoveRepository,
    BaseGameRepository,
)
from domain.games.value_objects import GameStatus


@dataclass
class DummyInMemoryGameRepository(BaseGameRepository):
    _saved_games: list[GameEntity] = field(default_factory=list, kw_only=True)

    async def add(self, game: GameEntity) -> None:
        self._saved_games.append(game)

    async def get_by_id(self, game_id: UUID) -> GameEntity | None:
        try:
            return next(game for game in self._saved_games if game.oid == game_id)
        except StopIteration:
            return None

    async def update(self, game: GameEntity) -> None:
        for idx, saved_game in enumerate(self._saved_games):
            if saved_game.oid == game.oid:
                self._saved_games[idx] = game
                return

    async def get_waiting_games(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]:
        waiting_games = [game for game in self._saved_games if game.status == GameStatus.WAITING]
        return waiting_games[offset : offset + limit]

    async def get_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]:
        user_games = [
            game
            for game in self._saved_games
            if (game.player_x_id == user_id or game.player_o_id == user_id)
            and (status is None or game.status == status)
        ]
        return user_games[offset : offset + limit]

    async def count_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
    ) -> int:
        user_games = [
            game
            for game in self._saved_games
            if (game.player_x_id == user_id or game.player_o_id == user_id)
            and (status is None or game.status == status)
        ]
        return len(user_games)


@dataclass
class DummyInMemoryGameMoveRepository(BaseGameMoveRepository):
    _saved_moves: list[GameMove] = field(default_factory=list, kw_only=True)

    async def add(self, move: GameMove) -> None:
        self._saved_moves.append(move)

    async def get_by_game_id(
        self,
        game_id: UUID,
    ) -> list[GameMove]:
        return sorted(
            [move for move in self._saved_moves if move.game_id == game_id],
            key=lambda m: m.move_number,
        )
