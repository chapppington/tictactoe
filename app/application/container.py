from functools import lru_cache

from infrastructure.database.gateways.postgres import SQLDatabase
from infrastructure.database.repositories.games.games import (
    MongoDBGameMoveRepository,
    MongoDBGamesRepository,
)
from infrastructure.database.repositories.users.users import SQLAlchemyUserRepository
from infrastructure.websockets.manager import (
    BaseConnectionManager,
    ConnectionManager,
)
from motor.motor_asyncio import AsyncIOMotorClient
from punq import (
    Container,
    Scope,
)

from application.games.commands import (
    CreateGameCommand,
    CreateGameCommandHandler,
    JoinGameCommand,
    JoinGameCommandHandler,
    MakeMoveCommand,
    MakeMoveCommandHandler,
)
from application.games.queries import (
    GetGameByIdQuery,
    GetGameByIdQueryHandler,
    GetGameMovesQuery,
    GetGameMovesQueryHandler,
    GetUserGamesQuery,
    GetUserGamesQueryHandler,
    GetWaitingGamesQuery,
    GetWaitingGamesQueryHandler,
)
from application.mediator import Mediator
from application.users.commands import (
    CreateUserCommand,
    CreateUserCommandHandler,
)
from application.users.queries import (
    AuthenticateUserQuery,
    AuthenticateUserQueryHandler,
    GetUserByIdQuery,
    GetUserByIdQueryHandler,
)
from domain.games.interfaces.repository import (
    BaseGameMoveRepository,
    BaseGameRepository,
)
from domain.games.services import GameService
from domain.users.interfaces.repository import BaseUserRepository
from domain.users.services import UserService
from settings.config import Config


@lru_cache(1)
def init_container():
    return _init_container()


def _init_container() -> Container:
    container = Container()

    # Регистрируем конфиг
    config = Config()
    container.register(Config, instance=config, scope=Scope.singleton)

    # WebSocket Manager
    container.register(
        BaseConnectionManager,
        instance=ConnectionManager(),
        scope=Scope.singleton,
    )

    # Регистрируем SQL Database
    def init_sql_database() -> SQLDatabase:
        return SQLDatabase(
            url=config.postgres_connection_uri,
            ro_url=config.postgres_connection_uri,
        )

    container.register(SQLDatabase, factory=init_sql_database, scope=Scope.singleton)

    # Регистрируем MongoDB Client
    def create_mongodb_client():
        return AsyncIOMotorClient(
            config.mongodb_connection_uri,
            serverSelectionTimeoutMS=3000,
        )

    container.register(
        AsyncIOMotorClient,
        factory=create_mongodb_client,
        scope=Scope.singleton,
    )

    # Регистрируем репозитории
    container.register(
        BaseUserRepository,
        SQLAlchemyUserRepository,
    )

    # Регистрируем репозитории игр
    def init_games_repository() -> MongoDBGamesRepository:
        return MongoDBGamesRepository(
            mongo_db_client=container.resolve(AsyncIOMotorClient),
            mongo_db_database_name=config.mongo_database,
            mongo_db_collection_name=config.mongodb_games_collection,
        )

    container.register(BaseGameRepository, factory=init_games_repository)

    def init_game_moves_repository() -> MongoDBGameMoveRepository:
        return MongoDBGameMoveRepository(
            mongo_db_client=container.resolve(AsyncIOMotorClient),
            mongo_db_database_name=config.mongo_database,
            mongo_db_collection_name=config.mongodb_game_moves_collection,
        )

    container.register(BaseGameMoveRepository, factory=init_game_moves_repository)

    # Регистрируем доменные сервисы
    container.register(UserService)
    container.register(GameService)

    # Регистрируем command handlers
    # Users
    container.register(CreateUserCommandHandler)

    # Games
    container.register(CreateGameCommandHandler)
    container.register(JoinGameCommandHandler)
    container.register(MakeMoveCommandHandler)

    # Регистрируем query handlers
    # Users
    container.register(AuthenticateUserQueryHandler)
    container.register(GetUserByIdQueryHandler)

    # Games
    container.register(GetGameByIdQueryHandler)
    container.register(GetWaitingGamesQueryHandler)
    container.register(GetUserGamesQueryHandler)
    container.register(GetGameMovesQueryHandler)

    # Инициализируем медиатор
    def init_mediator() -> Mediator:
        mediator = Mediator()

        # Регистрируем commands
        # Users
        mediator.register_command(
            CreateUserCommand,
            [container.resolve(CreateUserCommandHandler)],
        )

        # Games
        mediator.register_command(
            CreateGameCommand,
            [container.resolve(CreateGameCommandHandler)],
        )
        mediator.register_command(
            JoinGameCommand,
            [container.resolve(JoinGameCommandHandler)],
        )
        mediator.register_command(
            MakeMoveCommand,
            [container.resolve(MakeMoveCommandHandler)],
        )

        # Регистрируем queries
        # Users
        mediator.register_query(
            AuthenticateUserQuery,
            container.resolve(AuthenticateUserQueryHandler),
        )
        mediator.register_query(
            GetUserByIdQuery,
            container.resolve(GetUserByIdQueryHandler),
        )

        # Games
        mediator.register_query(
            GetGameByIdQuery,
            container.resolve(GetGameByIdQueryHandler),
        )
        mediator.register_query(
            GetWaitingGamesQuery,
            container.resolve(GetWaitingGamesQueryHandler),
        )
        mediator.register_query(
            GetUserGamesQuery,
            container.resolve(GetUserGamesQueryHandler),
        )
        mediator.register_query(
            GetGameMovesQuery,
            container.resolve(GetGameMovesQueryHandler),
        )

        return mediator

    container.register(Mediator, factory=init_mediator, scope=Scope.singleton)

    return container
