from fastapi import Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import InputValidationException, BusinessValidationException
from api.core.pagination import PaginatedResponse, PaginationParams, PaginationService
from api.domains.starships.models import Starship
from api.domains.starships.repository import StarshipRepository
from api.domains.starships.schemas import StarshipSchema
from api.storage.postgres import get_db_session


class StarshipService:
    def __init__(self, repository: StarshipRepository):
        self.repository = repository

    async def get_all_starships(
        self, session: AsyncSession, params: PaginationParams, name: str | None = None
    ) -> PaginatedResponse[StarshipSchema]:
        """Get paginated list of all starships with relationships loaded."""
        # Business logic validation for name parameter
        if name is not None:
            name = name.strip()
            if len(name) == 0:
                raise BusinessValidationException("Name cannot be empty", "name")
            if len(name) > 100:
                raise BusinessValidationException(
                    "Name cannot exceed 100 characters", "name"
                )

        pagination_service = PaginationService[StarshipSchema](session)

        def serialize_starships(starships: list[Starship]) -> list[StarshipSchema]:
            try:
                return [
                    StarshipSchema.model_validate(starship, from_attributes=True)
                    for starship in starships
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
                    serializer=serialize_starships,
                )
            else:
                return await pagination_service.paginate_with_repository(
                    repository_get_all=self.repository.get_all,
                    count_query_stmt=self.repository.get_count_query(),
                    params=params,
                    serializer=serialize_starships,
                )
        except Exception as e:
            # Re-raise known exceptions without wrapping
            if isinstance(e, (InputValidationException, BusinessValidationException)):
                raise
            # Let database exceptions bubble up as per project guidelines
            raise


def get_starship_service(
    session: AsyncSession = Depends(get_db_session),
) -> StarshipService:
    repository = StarshipRepository(session)
    return StarshipService(repository)
