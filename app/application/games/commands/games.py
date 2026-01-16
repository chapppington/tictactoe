from dataclasses import dataclass
from uuid import UUID

from application.base.command import (
    BaseCommand,
    BaseCommandHandler,
)
from domain.games.entities import GameEntity
from domain.games.services import GameService
from domain.games.value_objects import BoardPosition


@dataclass(frozen=True)
class CreateGameCommand(BaseCommand):
    player_x_id: UUID


@dataclass(frozen=True)
class CreateGameCommandHandler(
    BaseCommandHandler[CreateGameCommand, GameEntity],
):
    game_service: GameService

    async def handle(self, command: CreateGameCommand) -> GameEntity:
        return await self.game_service.create_game(player_x_id=command.player_x_id)


@dataclass(frozen=True)
class JoinGameCommand(BaseCommand):
    game_id: UUID
    player_o_id: UUID


@dataclass(frozen=True)
class JoinGameCommandHandler(
    BaseCommandHandler[JoinGameCommand, GameEntity],
):
    game_service: GameService

    async def handle(self, command: JoinGameCommand) -> GameEntity:
        return await self.game_service.join_game(
            game_id=command.game_id,
            player_o_id=command.player_o_id,
        )


@dataclass(frozen=True)
class MakeMoveCommand(BaseCommand):
    game_id: UUID
    player_id: UUID
    row: int
    col: int


@dataclass(frozen=True)
class MakeMoveCommandHandler(
    BaseCommandHandler[MakeMoveCommand, GameEntity],
):
    game_service: GameService

    async def handle(self, command: MakeMoveCommand) -> GameEntity:
        position = BoardPosition(value=(command.row, command.col))
        return await self.game_service.make_move(
            game_id=command.game_id,
            player_id=command.player_id,
            position=position,
        )
