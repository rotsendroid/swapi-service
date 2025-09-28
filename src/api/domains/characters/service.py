from typing import Optional

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination import PaginatedResponse, PaginationParams, PaginationService
from api.domains.characters.models import Character
from api.domains.characters.repository import CharacterRepository
from api.domains.characters.schemas import CharacterSchema
from api.storage.postgres import get_db_session


class CharacterService:
    def __init__(self, repository: CharacterRepository):
        self.repository = repository

    async def get_character_by_name(self, name: str) -> Optional[Character]:
        return await self.repository.get_by_name(name)

    async def get_all_characters(
        self, session: AsyncSession, params: PaginationParams
    ) -> PaginatedResponse[CharacterSchema]:
        """Get paginated list of all characters with relationships loaded."""
        pagination_service = PaginationService[CharacterSchema](session)

        def serialize_characters(characters: list[Character]) -> list[CharacterSchema]:
            return [
                CharacterSchema.model_validate(char, from_attributes=True)
                for char in characters
            ]

        return await pagination_service.paginate_with_repository(
            repository_get_all=self.repository.get_all,
            count_query_stmt=self.repository.get_count_query(),
            params=params,
            serializer=serialize_characters,
        )


def get_character_service(
    session: AsyncSession = Depends(get_db_session),
) -> CharacterService:
    repository = CharacterRepository(session)
    return CharacterService(repository)
