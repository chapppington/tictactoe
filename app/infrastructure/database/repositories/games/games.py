from dataclasses import dataclass
from uuid import UUID

from infrastructure.database.converters.games.game import (
    game_document_to_entity,
    game_entity_to_document,
    game_move_document_to_entity,
    game_move_entity_to_document,
)
from infrastructure.database.repositories.base.mongo import BaseMongoDBRepository

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
class MongoDBGamesRepository(BaseGameRepository, BaseMongoDBRepository):
    async def add(self, game: GameEntity) -> None:
        await self._collection.insert_one(game_entity_to_document(game))

    async def get_by_id(self, game_id: UUID) -> GameEntity | None:
        game_document = await self._collection.find_one(filter={"oid": str(game_id)})

        if not game_document:
            return None

        return game_document_to_entity(game_document)

    async def update(self, game: GameEntity) -> None:
        await self._collection.update_one(
            filter={"oid": str(game.oid)},
            update={"$set": game_entity_to_document(game)},
        )

    async def get_waiting_games(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]:
        cursor = (
            self._collection.find(
                filter={"status": GameStatus.WAITING.value},
            )
            .skip(offset)
            .limit(limit)
            .sort("created_at", -1)
        )

        games = []
        async for game_document in cursor:
            games.append(game_document_to_entity(game_document))

        return games

    async def get_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]:
        filter_query = {
            "$or": [
                {"player_x_id": str(user_id)},
                {"player_o_id": str(user_id)},
            ],
        }

        if status:
            filter_query["status"] = status.value

        cursor = (
            self._collection.find(
                filter=filter_query,
            )
            .skip(offset)
            .limit(limit)
            .sort("created_at", -1)
        )

        games = []
        async for game_document in cursor:
            games.append(game_document_to_entity(game_document))

        return games


@dataclass
class MongoDBGameMoveRepository(BaseGameMoveRepository, BaseMongoDBRepository):
    async def add(self, move: GameMove) -> None:
        await self._collection.insert_one(game_move_entity_to_document(move))

    async def get_by_game_id(
        self,
        game_id: UUID,
    ) -> list[GameMove]:
        cursor = self._collection.find(
            filter={"game_id": str(game_id)},
        ).sort("move_number", 1)

        moves = []
        async for move_document in cursor:
            moves.append(game_move_document_to_entity(move_document))

        return moves
