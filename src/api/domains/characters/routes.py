from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.exceptions import (
    DatabaseException,
    InputValidationException,
    BusinessValidationException,
)
from api.core.pagination import PaginatedResponse, PaginationParams
from api.domains.characters.schemas import CharacterSchema
from api.domains.characters.service import CharacterService, get_character_service
from api.storage.postgres import get_db_session

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get(
    "/",
    response_model=PaginatedResponse[CharacterSchema],
    responses={
        400: BusinessValidationException.response_example(),
        422: InputValidationException.response_example(),
        500: DatabaseException.response_example(),
    },
)
async def get_all_characters(
    offset: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        default=10, ge=1, le=100, description="Number of items to return"
    ),
    name: str | None = Query(default=None, description="Filter characters by name"),
    session: AsyncSession = Depends(get_db_session),
    service: CharacterService = Depends(get_character_service),
) -> PaginatedResponse[CharacterSchema]:  # pragma: no cover
    """Get paginated list of all characters."""
    params = PaginationParams(offset=offset, limit=limit)
    return await service.get_all_characters(session, params, name)
