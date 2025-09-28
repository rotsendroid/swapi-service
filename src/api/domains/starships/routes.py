from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination import PaginatedResponse, PaginationParams
from api.domains.starships.schemas import StarshipSchema
from api.domains.starships.service import StarshipService, get_starship_service
from api.storage.postgres import get_db_session

router = APIRouter(prefix="/starships", tags=["starships"])


@router.get("/", response_model=PaginatedResponse[StarshipSchema])
async def get_all_starships(
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of items to return"
    ),
    name: str | None = Query(default=None, description="Filter starships by name"),
    session: AsyncSession = Depends(get_db_session),
    service: StarshipService = Depends(get_starship_service),
) -> PaginatedResponse[StarshipSchema]:
    """Get paginated list of all starships."""
    params = PaginationParams(offset=offset, limit=limit)
    return await service.get_all_starships(session, params, name)
