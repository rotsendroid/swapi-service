from fastapi import APIRouter, Depends

from api.core.exceptions import (
    ExternalServiceException,
    InputValidationException,
    InternalServerException,
)
from api.core.populatedb.schemas import PopulateDBResponse
from api.core.populatedb.service import PopulateDBService

router = APIRouter()


@router.post(
    "/populatedb",
    response_model=PopulateDBResponse,
    responses={
        422: InputValidationException.response_example(),
        500: InternalServerException.response_example(),
        502: ExternalServiceException.response_example(),
    },
)
async def populate_database_endpoint(
    service: PopulateDBService = Depends(),
):  # pragma: no cover
    """Populate database with SWAPI data."""
    return await service.populatedb_wrapper()
