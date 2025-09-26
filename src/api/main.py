from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.lifespan import lifespan
from api.core.middleware import RequestLoggingMiddleware, ExceptionHandlerMiddleware
from api.storage.postgres import get_db_session
from api.utils.healthcheck import HealthCheckResponse, perform_health_check

app = FastAPI(title="SWAPI-Service", lifespan=lifespan)

app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(RequestLoggingMiddleware)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check(
    db: AsyncSession = Depends(get_db_session),
) -> HealthCheckResponse:
    """Health check endpoint that verifies FastAPI, PostgreSQL, and SWAPI external API connectivity."""
    return await perform_health_check(db)
