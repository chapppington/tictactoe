from infrastructure.database.repositories.dummy.games.games import (
    DummyInMemoryGameMoveRepository,
    DummyInMemoryGameRepository,
)
from infrastructure.database.repositories.dummy.users.users import DummyInMemoryUserRepository
from punq import (
    Container,
    Scope,
)

from application.container import _init_container
from domain.games.interfaces.repository import (
    BaseGameMoveRepository,
    BaseGameRepository,
)
from domain.users.interfaces.repository import BaseUserRepository


def init_dummy_container() -> Container:
    container = _init_container()

    # Регистрируем dummy репозитории как синглтоны
    container.register(
        BaseUserRepository,
        DummyInMemoryUserRepository,
        scope=Scope.singleton,
    )
    container.register(
        BaseGameRepository,
        DummyInMemoryGameRepository,
        scope=Scope.singleton,
    )
    container.register(
        BaseGameMoveRepository,
        DummyInMemoryGameMoveRepository,
        scope=Scope.singleton,
    )

    return container
