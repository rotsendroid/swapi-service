from fastapi import Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import InputValidationException, BusinessValidationException
from api.core.pagination import PaginatedResponse, PaginationParams, PaginationService
from api.domains.films.models import Film
from api.domains.films.repository import FilmRepository
from api.domains.films.schemas import FilmSchema
from api.storage.postgres import get_db_session


class FilmService:
    def __init__(self, repository: FilmRepository):
        self.repository = repository

    async def get_all_films(
        self, session: AsyncSession, params: PaginationParams, title: str | None = None
    ) -> PaginatedResponse[FilmSchema]:
        """Get paginated list of all films with relationships loaded."""
        # Business logic validation for title parameter
        if title is not None:
            title = title.strip()
            if len(title) == 0:
                raise BusinessValidationException("Title cannot be empty", "title")
            if len(title) > 100:
                raise BusinessValidationException(
                    "Title cannot exceed 100 characters", "title"
                )

        pagination_service = PaginationService[FilmSchema](session)

        def serialize_films(films: list[Film]) -> list[FilmSchema]:
            try:
                return [
                    FilmSchema.model_validate(film, from_attributes=True)
                    for film in films
                ]
            except ValidationError as e:
                raise InputValidationException(e) from e

        try:
            if title:
                return await pagination_service.paginate_with_repository(
                    repository_get_all=lambda skip, limit: self.repository.get_by_title(
                        title, skip, limit
                    ),
                    count_query_stmt=self.repository.get_count_query(title),
                    params=params,
                    serializer=serialize_films,
                )
            else:
                return await pagination_service.paginate_with_repository(
                    repository_get_all=self.repository.get_all,
                    count_query_stmt=self.repository.get_count_query(),
                    params=params,
                    serializer=serialize_films,
                )
        except Exception as e:
            # Re-raise known exceptions without wrapping
            if isinstance(e, (InputValidationException, BusinessValidationException)):
                raise
            # Let database exceptions bubble up as per project guidelines
            raise


def get_film_service(
    session: AsyncSession = Depends(get_db_session),
) -> FilmService:
    repository = FilmRepository(session)
    return FilmService(repository)
