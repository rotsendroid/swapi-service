from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination import PaginatedResponse, PaginationParams
from api.domains.films.schemas import FilmSchema
from api.domains.films.service import FilmService, get_film_service
from api.storage.postgres import get_db_session

router = APIRouter(prefix="/films", tags=["films"])


@router.get("/", response_model=PaginatedResponse[FilmSchema])
async def get_all_films(
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of items to return"
    ),
    title: str | None = Query(default=None, description="Filter films by title"),
    session: AsyncSession = Depends(get_db_session),
    service: FilmService = Depends(get_film_service),
) -> PaginatedResponse[FilmSchema]:
    """Get paginated list of all films."""
    params = PaginationParams(offset=offset, limit=limit)
    return await service.get_all_films(session, params, title)
