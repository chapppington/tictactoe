from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.exceptions import (
    GameAlreadyFinishedException,
    GameAlreadyFullException,
    GameNotFoundException,
    InvalidMoveException,
    NotPlayerTurnException,
)
from domain.games.interfaces.repository import (
    BaseGameMoveRepository,
    BaseGameRepository,
)
from domain.games.value_objects import (
    BoardPosition,
    GameStatus,
    PlayerSymbol,
)


@dataclass
class GameService:
    game_repository: BaseGameRepository
    game_move_repository: BaseGameMoveRepository

    async def create_game(self, player_x_id: UUID) -> GameEntity:
        game = GameEntity(player_x_id=player_x_id, status=GameStatus.WAITING)
        await self.game_repository.add(game)
        return game

    async def get_by_id(self, game_id: UUID) -> GameEntity:
        game = await self.game_repository.get_by_id(game_id)
        if not game:
            raise GameNotFoundException(game_id=game_id)
        return game

    async def join_game(self, game_id: UUID, player_o_id: UUID) -> GameEntity:
        game = await self.get_by_id(game_id)

        if game.is_full():
            raise GameAlreadyFullException(game_id=game_id)

        if game.status == GameStatus.FINISHED:
            raise GameAlreadyFinishedException(game_id=game_id)

        if game.status != GameStatus.WAITING:
            raise GameAlreadyFinishedException(game_id=game_id)

        if game.player_x_id == player_o_id:
            raise InvalidMoveException(
                game_id=game_id,
                reason="Cannot join your own game",
            )

        game.player_o_id = player_o_id
        game.status = GameStatus.ACTIVE
        await self.game_repository.update(game)

        return game

    async def make_move(
        self,
        game_id: UUID,
        player_id: UUID,
        position: BoardPosition,
    ) -> GameEntity:
        game = await self.get_by_id(game_id)

        if not game.is_full():
            raise InvalidMoveException(
                game_id=game_id,
                reason="Game is not full yet",
            )

        if game.status == GameStatus.FINISHED:
            raise GameAlreadyFinishedException(game_id=game_id)

        if game.status != GameStatus.ACTIVE:
            raise GameAlreadyFinishedException(game_id=game_id)

        if player_id not in (game.player_x_id, game.player_o_id):
            raise InvalidMoveException(
                game_id=game_id,
                reason="Player is not part of this game",
            )

        expected_symbol = PlayerSymbol.X if player_id == game.player_x_id else PlayerSymbol.O
        if game.current_turn != expected_symbol:
            raise NotPlayerTurnException(game_id=game_id, player_id=player_id)

        if not game.is_position_empty(position.row, position.col):
            raise InvalidMoveException(
                game_id=game_id,
                reason=f"Position ({position.row}, {position.col}) is already occupied",
            )

        moves_count = len(await self.game_move_repository.get_by_game_id(game_id))
        move = GameMove(
            game_id=game_id,
            player_id=player_id,
            row=position.row,
            col=position.col,
            symbol=expected_symbol,
            move_number=moves_count + 1,
        )
        await self.game_move_repository.add(move)

        game.make_move(player_id, position)

        winner_symbol = game.check_winner()
        if winner_symbol:
            game.status = GameStatus.FINISHED
            game.winner_id = game.get_winner_id()
            game.finished_at = datetime.now()
        elif game.is_board_full():
            game.status = GameStatus.FINISHED
            game.finished_at = datetime.now()

        await self.game_repository.update(game)

        return game

    async def get_waiting_games(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]:
        return await self.game_repository.get_waiting_games(limit=limit, offset=offset)

    async def get_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[GameEntity]:
        return await self.game_repository.get_user_games(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def count_user_games(
        self,
        user_id: UUID,
        status: GameStatus | None = None,
    ) -> int:
        return await self.game_repository.count_user_games(
            user_id=user_id,
            status=status,
        )

    async def get_game_moves(self, game_id: UUID) -> list[GameMove]:
        await self.get_by_id(game_id)
        return await self.game_move_repository.get_by_game_id(game_id)
