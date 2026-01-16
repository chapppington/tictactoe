from dataclasses import dataclass
from uuid import UUID

from application.base.query import (
    BaseQuery,
    BaseQueryHandler,
)
from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.services import GameService
from domain.games.value_objects import GameStatus


@dataclass(frozen=True)
class GetGameByIdQuery(BaseQuery):
    game_id: UUID


@dataclass(frozen=True)
class GetGameByIdQueryHandler(
    BaseQueryHandler[GetGameByIdQuery, GameEntity],
):
    game_service: GameService

    async def handle(self, query: GetGameByIdQuery) -> GameEntity:
        return await self.game_service.get_by_id(game_id=query.game_id)


@dataclass(frozen=True)
class GetWaitingGamesQuery(BaseQuery):
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetWaitingGamesQueryHandler(
    BaseQueryHandler[GetWaitingGamesQuery, list[GameEntity]],
):
    game_service: GameService

    async def handle(self, query: GetWaitingGamesQuery) -> list[GameEntity]:
        return await self.game_service.get_waiting_games(
            limit=query.limit,
            offset=query.offset,
        )


@dataclass(frozen=True)
class GetUserGamesQuery(BaseQuery):
    user_id: UUID
    status: GameStatus | None = None
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True)
class GetUserGamesQueryHandler(
    BaseQueryHandler[GetUserGamesQuery, list[GameEntity]],
):
    game_service: GameService

    async def handle(self, query: GetUserGamesQuery) -> list[GameEntity]:
        return await self.game_service.get_user_games(
            user_id=query.user_id,
            status=query.status,
            limit=query.limit,
            offset=query.offset,
        )


@dataclass(frozen=True)
class GetGameMovesQuery(BaseQuery):
    game_id: UUID


@dataclass(frozen=True)
class GetGameMovesQueryHandler(
    BaseQueryHandler[GetGameMovesQuery, list[GameMove]],
):
    game_service: GameService

    async def handle(self, query: GetGameMovesQuery) -> list[GameMove]:
        return await self.game_service.get_game_moves(game_id=query.game_id)
