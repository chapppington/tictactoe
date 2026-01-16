from uuid import UUID

from pydantic import BaseModel

from domain.users.entities import UserEntity


class UserResponseSchema(BaseModel):
    oid: UUID
    email: str
    name: str

    @classmethod
    def from_entity(cls, entity: UserEntity) -> "UserResponseSchema":
        return cls(
            oid=entity.oid,
            email=entity.email.as_generic_type(),
            name=entity.name.as_generic_type(),
        )
