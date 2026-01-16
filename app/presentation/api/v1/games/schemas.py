from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.value_objects import (
    GameStatus,
    PlayerSymbol,
)


class BoardPositionSchema(BaseModel):
    row: int
    col: int


class GameResponseSchema(BaseModel):
    oid: UUID
    player_x_id: UUID
    player_o_id: Optional[UUID] = None
    status: GameStatus
    board: list[list[Optional[str]]]
    current_turn: PlayerSymbol
    winner_id: Optional[UUID] = None
    finished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: GameEntity) -> "GameResponseSchema":
        board_serialized = [[cell.value if cell else None for cell in row] for row in entity.board]
        return cls(
            oid=entity.oid,
            player_x_id=entity.player_x_id,
            player_o_id=entity.player_o_id,
            status=entity.status,
            board=board_serialized,
            current_turn=entity.current_turn,
            winner_id=entity.winner_id,
            finished_at=entity.finished_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class GameMoveResponseSchema(BaseModel):
    oid: UUID
    game_id: UUID
    player_id: UUID
    row: int
    col: int
    symbol: PlayerSymbol
    move_number: int
    created_at: datetime

    @classmethod
    def from_entity(cls, entity: GameMove) -> "GameMoveResponseSchema":
        return cls(
            oid=entity.oid,
            game_id=entity.game_id,
            player_id=entity.player_id,
            row=entity.row,
            col=entity.col,
            symbol=entity.symbol,
            move_number=entity.move_number,
            created_at=entity.created_at,
        )


class CreateGameRequestSchema(BaseModel):
    pass


class JoinGameRequestSchema(BaseModel):
    pass


class MakeMoveRequestSchema(BaseModel):
    row: int
    col: int
