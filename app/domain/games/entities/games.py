from dataclasses import (
    dataclass,
    field,
)
from datetime import datetime
from typing import Optional
from uuid import UUID

from domain.base.entity import BaseEntity
from domain.games.value_objects import (
    BoardPosition,
    GameStatus,
    PlayerSymbol,
)


@dataclass(eq=False)
class GameMove(BaseEntity):
    game_id: UUID
    player_id: UUID
    row: int
    col: int
    symbol: PlayerSymbol
    move_number: int


@dataclass(eq=False)
class GameEntity(BaseEntity):
    player_x_id: UUID
    player_o_id: Optional[UUID] = None
    status: GameStatus = GameStatus.WAITING
    board: list[list[Optional[PlayerSymbol]]] = field(
        default_factory=lambda: [[None for _ in range(3)] for _ in range(3)],
    )
    current_turn: PlayerSymbol = PlayerSymbol.X
    winner_id: Optional[UUID] = None
    finished_at: Optional[datetime] = None

    def is_full(self) -> bool:
        return self.player_o_id is not None

    def is_position_empty(self, row: int, col: int) -> bool:
        return self.board[row][col] is None

    def make_move(self, player_id: UUID, position: BoardPosition) -> None:
        if not self.is_position_empty(position.row, position.col):
            return

        symbol = PlayerSymbol.X if player_id == self.player_x_id else PlayerSymbol.O
        self.board[position.row][position.col] = symbol
        self.current_turn = PlayerSymbol.O if self.current_turn == PlayerSymbol.X else PlayerSymbol.X

    def check_winner(self) -> Optional[PlayerSymbol]:
        board = self.board

        for i in range(3):
            if board[i][0] and board[i][0] == board[i][1] == board[i][2]:
                return board[i][0]
            if board[0][i] and board[0][i] == board[1][i] == board[2][i]:
                return board[0][i]

        if board[0][0] and board[0][0] == board[1][1] == board[2][2]:
            return board[0][0]
        if board[0][2] and board[0][2] == board[1][1] == board[2][0]:
            return board[0][2]

        return None

    def is_board_full(self) -> bool:
        return all(cell is not None for row in self.board for cell in row)

    def get_winner_id(self) -> Optional[UUID]:
        winner_symbol = self.check_winner()
        if winner_symbol == PlayerSymbol.X:
            return self.player_x_id
        if winner_symbol == PlayerSymbol.O:
            return self.player_o_id
        return None
