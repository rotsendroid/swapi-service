from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.lifespan import lifespan
from api.core.middleware import ExceptionHandlerMiddleware, RequestLoggingMiddleware
from api.core.populatedb.routes import router as populatedb_router
from api.domains.characters.routes import router as characters_router
from api.domains.films.routes import router as films_router
from api.domains.starships.routes import router as starships_router
from api.storage.postgres import get_db_session
from api.utils.healthcheck import HealthCheckResponse, perform_health_check

app = FastAPI(title="SWAPI-Service", lifespan=lifespan)

app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(populatedb_router)
app.include_router(characters_router)
app.include_router(films_router)
app.include_router(starships_router)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> HealthCheckResponse:
    """Health check endpoint that verifies FastAPI, PostgreSQL, and SWAPI external API connectivity."""
    return await perform_health_check(db)
