from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from presentation.api.dependencies import get_current_user_id
from presentation.api.schemas import (
    ApiResponse,
    ErrorResponseSchema,
)
from presentation.api.v1.users.schemas import UserResponseSchema

from application.container import init_container
from application.mediator import Mediator
from application.users.queries import GetUserByIdQuery


router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[UserResponseSchema],
    responses={
        status.HTTP_200_OK: {"model": ApiResponse[UserResponseSchema]},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponseSchema},
    },
)
async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    container=Depends(init_container),
) -> ApiResponse[UserResponseSchema]:
    """Получение информации о текущем пользователе."""
    mediator: Mediator = container.resolve(Mediator)

    query = GetUserByIdQuery(user_id=user_id)
    user = await mediator.handle_query(query)

    return ApiResponse[UserResponseSchema](
        data=UserResponseSchema.from_entity(user),
    )
