from fastapi import Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import InputValidationException, BusinessValidationException
from api.core.pagination import PaginatedResponse, PaginationParams, PaginationService
from api.domains.characters.models import Character
from api.domains.characters.repository import CharacterRepository
from api.domains.characters.schemas import CharacterSchema
from api.storage.postgres import get_db_session


class CharacterService:
    def __init__(self, repository: CharacterRepository):
        self.repository = repository

    async def get_all_characters(
        self, session: AsyncSession, params: PaginationParams, name: str | None = None
    ) -> PaginatedResponse[CharacterSchema]:
        """Get paginated list of all characters with relationships loaded."""
        # Business logic validation for name parameter
        if name is not None:
            name = name.strip()
            if len(name) == 0:
                raise BusinessValidationException("Name cannot be empty", "name")
            if len(name) > 100:
                raise BusinessValidationException(
                    "Name cannot exceed 100 characters", "name"
                )

        pagination_service = PaginationService[CharacterSchema](session)

        def serialize_characters(characters: list[Character]) -> list[CharacterSchema]:
            try:
                return [
                    CharacterSchema.model_validate(char, from_attributes=True)
                    for char in characters
                ]
            except ValidationError as e:
                raise InputValidationException(e) from e

        try:
            if name:
                return await pagination_service.paginate_with_repository(
                    repository_get_all=lambda skip, limit: self.repository.get_by_name(
                        name, skip, limit
                    ),
                    count_query_stmt=self.repository.get_count_query(name),
                    params=params,
                    serializer=serialize_characters,
                )
            else:
                return await pagination_service.paginate_with_repository(
                    repository_get_all=self.repository.get_all,
                    count_query_stmt=self.repository.get_count_query(),
                    params=params,
                    serializer=serialize_characters,
                )
        except Exception as e:
            # Re-raise known exceptions without wrapping
            if isinstance(e, (InputValidationException, BusinessValidationException)):
                raise
            # Let database exceptions bubble up as per project guidelines
            raise


def get_character_service(
    session: AsyncSession = Depends(get_db_session),
) -> CharacterService:
    repository = CharacterRepository(session)
    return CharacterService(repository)
