from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
        pagination_service = PaginationService[StarshipSchema](session)

        def serialize_starships(starships: list[Starship]) -> list[StarshipSchema]:
            return [
                StarshipSchema.model_validate(starship, from_attributes=True)
                for starship in starships
            ]

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


def get_starship_service(
    session: AsyncSession = Depends(get_db_session),
) -> StarshipService:
    repository = StarshipRepository(session)
    return StarshipService(repository)
