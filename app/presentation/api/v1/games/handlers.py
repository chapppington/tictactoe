from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
    WebSocket,
    WebSocketDisconnect,
)

from infrastructure.websockets.manager import BaseConnectionManager
from presentation.api.dependencies import (
    get_current_user_id,
    get_current_user_id_from_websocket,
)
from presentation.api.filters import PaginationOut
from presentation.api.schemas import (
    ApiResponse,
    ErrorResponseSchema,
    ListPaginatedResponse,
)
from presentation.api.v1.games.schemas import (
    CreateGameRequestSchema,
    GameMoveResponseSchema,
    GameResponseSchema,
    JoinGameRequestSchema,
    MakeMoveRequestSchema,
)

from application.container import init_container
from application.games.commands import (
    CreateGameCommand,
    JoinGameCommand,
    MakeMoveCommand,
)
from application.games.queries import (
    GetGameByIdQuery,
    GetGameMovesQuery,
    GetUserGamesQuery,
    GetWaitingGamesQuery,
)
from application.mediator import Mediator
from domain.games.value_objects import GameStatus


router = APIRouter(prefix="/games", tags=["games"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[GameResponseSchema],
    responses={
        status.HTTP_201_CREATED: {"model": ApiResponse[GameResponseSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
    },
)
async def create_game(
    request: CreateGameRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    container=Depends(init_container),
) -> ApiResponse[GameResponseSchema]:
    """Создание новой игры."""
    mediator: Mediator = container.resolve(Mediator)

    command = CreateGameCommand(player_x_id=user_id)
    game, *_ = await mediator.handle_command(command)

    # Отправляем обновление через WebSocket для участников игры
    await _send_game_update(
        game_id=game.oid,
        event_type="game_created",
        data=GameResponseSchema.from_entity(game).model_dump(mode="json"),
        container=container,
    )

    # Отправляем уведомление о новой ожидающей игре всем подписанным
    if game.status == GameStatus.WAITING:
        await _send_waiting_games_update(
            event_type="new_waiting_game",
            data=GameResponseSchema.from_entity(game).model_dump(mode="json"),
            container=container,
        )

    return ApiResponse[GameResponseSchema](
        data=GameResponseSchema.from_entity(game),
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ListPaginatedResponse[GameResponseSchema]],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[ListPaginatedResponse[GameResponseSchema]]},
    },
)
async def get_waiting_games(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    container=Depends(init_container),
) -> ApiResponse[ListPaginatedResponse[GameResponseSchema]]:
    """Получение списка ожидающих игр."""
    mediator: Mediator = container.resolve(Mediator)

    query = GetWaitingGamesQuery(limit=limit, offset=offset)
    games = await mediator.handle_query(query)

    return ApiResponse[ListPaginatedResponse[GameResponseSchema]](
        data=ListPaginatedResponse[GameResponseSchema](
            items=[GameResponseSchema.from_entity(game) for game in games],
            pagination=PaginationOut(
                limit=limit,
                offset=offset,
                total=len(games),
            ),
        ),
    )


@router.get(
    "/my",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[ListPaginatedResponse[GameResponseSchema]],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[ListPaginatedResponse[GameResponseSchema]]},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
    },
)
async def get_my_games(
    status_filter: GameStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    container=Depends(init_container),
) -> ApiResponse[ListPaginatedResponse[GameResponseSchema]]:
    """Получение списка игр текущего пользователя."""
    mediator: Mediator = container.resolve(Mediator)

    query = GetUserGamesQuery(
        user_id=user_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    games, total = await mediator.handle_query(query)

    return ApiResponse[ListPaginatedResponse[GameResponseSchema]](
        data=ListPaginatedResponse[GameResponseSchema](
            items=[GameResponseSchema.from_entity(game) for game in games],
            pagination=PaginationOut(
                limit=limit,
                offset=offset,
                total=total,
            ),
        ),
    )


@router.get(
    "/{game_id}",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[GameResponseSchema],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[GameResponseSchema]},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
    },
)
async def get_game(
    game_id: UUID,
    container=Depends(init_container),
) -> ApiResponse[GameResponseSchema]:
    """Получение информации об игре."""
    mediator: Mediator = container.resolve(Mediator)

    query = GetGameByIdQuery(game_id=game_id)
    game = await mediator.handle_query(query)

    return ApiResponse[GameResponseSchema](
        data=GameResponseSchema.from_entity(game),
    )


@router.post(
    "/{game_id}/join",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[GameResponseSchema],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[GameResponseSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
    },
)
async def join_game(
    game_id: UUID,
    request: JoinGameRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    container=Depends(init_container),
) -> ApiResponse[GameResponseSchema]:
    """Присоединение к игре."""
    mediator: Mediator = container.resolve(Mediator)

    command = JoinGameCommand(game_id=game_id, player_o_id=user_id)
    game, *_ = await mediator.handle_command(command)

    # Отправляем обновление через WebSocket для участников игры
    await _send_game_update(
        game_id=game_id,
        event_type="player_joined",
        data={
            "game": GameResponseSchema.from_entity(game).model_dump(mode="json"),
            "player_id": str(user_id),
        },
        container=container,
    )

    # Уведомляем что игра больше не ожидает (удалена из списка ожидающих)
    await _send_waiting_games_update(
        event_type="waiting_game_removed",
        data={"game_id": str(game_id)},
        container=container,
    )

    return ApiResponse[GameResponseSchema](
        data=GameResponseSchema.from_entity(game),
    )


@router.post(
    "/{game_id}/move",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[GameResponseSchema],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[GameResponseSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
    },
)
async def make_move(
    game_id: UUID,
    request: MakeMoveRequestSchema,
    user_id: UUID = Depends(get_current_user_id),
    container=Depends(init_container),
) -> ApiResponse[GameResponseSchema]:
    """Выполнение хода в игре."""
    mediator: Mediator = container.resolve(Mediator)

    command = MakeMoveCommand(
        game_id=game_id,
        player_id=user_id,
        row=request.row,
        col=request.col,
    )
    game, *_ = await mediator.handle_command(command)

    # Отправляем обновление через WebSocket
    event_type = "game_finished" if game.status == GameStatus.FINISHED else "move_made"
    await _send_game_update(
        game_id=game_id,
        event_type=event_type,
        data={
            "game": GameResponseSchema.from_entity(game).model_dump(mode="json"),
            "move": {
                "row": request.row,
                "col": request.col,
                "player_id": str(user_id),
            },
        },
        container=container,
    )

    return ApiResponse[GameResponseSchema](
        data=GameResponseSchema.from_entity(game),
    )


@router.get(
    "/{game_id}/moves",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[list[GameMoveResponseSchema]],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[list[GameMoveResponseSchema]]},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponseSchema},
    },
)
async def get_game_moves(
    game_id: UUID,
    container=Depends(init_container),
) -> ApiResponse[list[GameMoveResponseSchema]]:
    """Получение истории ходов игры."""
    mediator: Mediator = container.resolve(Mediator)

    query = GetGameMovesQuery(game_id=game_id)
    moves = await mediator.handle_query(query)

    return ApiResponse[list[GameMoveResponseSchema]](
        data=[GameMoveResponseSchema.from_entity(move) for move in moves],
    )


async def _send_game_update(
    game_id: UUID,
    event_type: str,
    data: dict,
    container,
):
    """Отправка обновления игры через WebSocket."""
    connection_manager: BaseConnectionManager = container.resolve(BaseConnectionManager)
    await connection_manager.send_json_to_all(
        key=str(game_id),
        data={
            "event": event_type,
            "game_id": str(game_id),
            "data": data,
        },
    )


async def _send_waiting_games_update(
    event_type: str,
    data: dict,
    container,
):
    """Отправка обновления списка ожидающих игр через WebSocket."""
    connection_manager: BaseConnectionManager = container.resolve(BaseConnectionManager)
    await connection_manager.send_json_to_all(
        key="waiting_games",
        data={
            "event": event_type,
            "data": data,
        },
    )


@router.websocket("/waiting-games/ws")
async def websocket_waiting_games(
    websocket: WebSocket,
    user_id: UUID = Depends(get_current_user_id_from_websocket),
    container=Depends(init_container),
):
    """WebSocket endpoint для получения уведомлений о новых ожидающих играх."""
    await websocket.accept()

    connection_manager: BaseConnectionManager = container.resolve(BaseConnectionManager)

    await connection_manager.accept_connection(websocket=websocket, key="waiting_games")

    try:
        while True:
            message = await websocket.receive_json()

            if message.get("event") == "ping":
                await websocket.send_json({"event": "pong"})
            else:
                await websocket.send_json(
                    {
                        "event": "error",
                        "data": {"message": "Unknown event"},
                    },
                )
    except WebSocketDisconnect:
        await connection_manager.remove_connection(websocket=websocket, key="waiting_games")


@router.websocket("/{game_id}/ws")
async def websocket_game(
    game_id: UUID,
    websocket: WebSocket,
    user_id: UUID = Depends(get_current_user_id_from_websocket),
    container=Depends(init_container),
):
    """WebSocket endpoint для игры с авторизацией."""
    # Принимаем соединение после успешной авторизации через dependency
    await websocket.accept()

    mediator: Mediator = container.resolve(Mediator)
    connection_manager: BaseConnectionManager = container.resolve(BaseConnectionManager)

    # Проверяем, что пользователь является участником игры
    try:
        query = GetGameByIdQuery(game_id=game_id)
        game = await mediator.handle_query(query)

        if user_id not in (game.player_x_id, game.player_o_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not a game participant")
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Game not found")
        return

    await connection_manager.accept_connection(websocket=websocket, key=str(game_id))

    # Отправляем текущее состояние игры при подключении
    await websocket.send_json(
        {
            "event": "game_state",
            "game_id": str(game_id),
            "data": GameResponseSchema.from_entity(game).model_dump(mode="json"),
        },
    )

    try:
        while True:
            message = await websocket.receive_json()

            if message.get("event") == "ping":
                await websocket.send_json({"event": "pong"})
            else:
                await websocket.send_json(
                    {
                        "event": "error",
                        "game_id": str(game_id),
                        "data": {"message": "Unknown event"},
                    },
                )
    except WebSocketDisconnect:
        await connection_manager.remove_connection(websocket=websocket, key=str(game_id))
