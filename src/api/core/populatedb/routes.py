from fastapi import APIRouter, Depends

from api.core.populatedb.schemas import PopulateDBResponse
from api.core.populatedb.service import PopulateDBService

router = APIRouter()


@router.post("/populatedb", response_model=PopulateDBResponse)
async def populate_database_endpoint(service: PopulateDBService = Depends()):
    """Populate database with SWAPI data."""
    return await service.populatedb_wrapper()
