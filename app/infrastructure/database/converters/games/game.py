from datetime import datetime
from uuid import UUID

from domain.games.entities import (
    GameEntity,
    GameMove,
)
from domain.games.value_objects import (
    GameStatus,
    PlayerSymbol,
)


def game_entity_to_document(entity: GameEntity) -> dict:
    board_serialized = [[cell.value if cell else None for cell in row] for row in entity.board]

    return {
        "oid": str(entity.oid),
        "player_x_id": str(entity.player_x_id),
        "player_o_id": str(entity.player_o_id) if entity.player_o_id else None,
        "status": entity.status.value,
        "board": board_serialized,
        "current_turn": entity.current_turn.value,
        "winner_id": str(entity.winner_id) if entity.winner_id else None,
        "finished_at": entity.finished_at.isoformat() if entity.finished_at else None,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat(),
    }


def game_document_to_entity(document: dict) -> GameEntity:
    board_deserialized = [[PlayerSymbol(cell) if cell else None for cell in row] for row in document["board"]]

    return GameEntity(
        oid=UUID(document["oid"]),
        player_x_id=UUID(document["player_x_id"]),
        player_o_id=UUID(document["player_o_id"]) if document.get("player_o_id") else None,
        status=GameStatus(document["status"]),
        board=board_deserialized,
        current_turn=PlayerSymbol(document["current_turn"]),
        winner_id=UUID(document["winner_id"]) if document.get("winner_id") else None,
        finished_at=datetime.fromisoformat(document["finished_at"]) if document.get("finished_at") else None,
        created_at=datetime.fromisoformat(document["created_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
    )


def game_move_entity_to_document(entity: GameMove) -> dict:
    return {
        "oid": str(entity.oid),
        "game_id": str(entity.game_id),
        "player_id": str(entity.player_id),
        "row": entity.row,
        "col": entity.col,
        "symbol": entity.symbol.value,
        "move_number": entity.move_number,
        "created_at": entity.created_at.isoformat(),
        "updated_at": entity.updated_at.isoformat(),
    }


def game_move_document_to_entity(document: dict) -> GameMove:
    return GameMove(
        oid=UUID(document["oid"]),
        game_id=UUID(document["game_id"]),
        player_id=UUID(document["player_id"]),
        row=document["row"],
        col=document["col"],
        symbol=PlayerSymbol(document["symbol"]),
        move_number=document["move_number"],
        created_at=datetime.fromisoformat(document["created_at"]),
        updated_at=datetime.fromisoformat(document["updated_at"]),
    )
