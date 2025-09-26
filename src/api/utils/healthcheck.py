from enum import Enum

import aiohttp
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.settings import get_settings


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class ServiceStatus(str, Enum):
    """Individual service status values."""

    OK = "ok"
    ERROR = "error"
    UNKNOWN = "unknown"


class HealthCheckResponse(BaseModel):
    status: HealthStatus
    fastapi: ServiceStatus
    postgres: ServiceStatus
    swapi_external: ServiceStatus


async def perform_health_check(db: AsyncSession) -> HealthCheckResponse:
    """Perform comprehensive health check of all services."""
    settings = get_settings()

    # Test database connection
    postgres_status = ServiceStatus.UNKNOWN
    try:
        result = await db.execute(text("SELECT 1"))
        result.fetchone()
        postgres_status = ServiceStatus.OK
    except Exception:
        postgres_status = ServiceStatus.ERROR

    # Test SWAPI external API
    swapi_status = ServiceStatus.UNKNOWN
    try:
        timeout = aiohttp.ClientTimeout(total=5.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(settings.swapi_status_url) as resp:
                if resp.status == 200:
                    swapi_status = ServiceStatus.OK
                else:
                    swapi_status = ServiceStatus.ERROR
    except Exception:
        swapi_status = ServiceStatus.ERROR

    # Determine overall status
    overall_status = (
        HealthStatus.HEALTHY
        if postgres_status == ServiceStatus.OK and swapi_status == ServiceStatus.OK
        else HealthStatus.UNHEALTHY
    )

    return HealthCheckResponse(
        status=overall_status,
        fastapi=ServiceStatus.OK,
        postgres=postgres_status,
        swapi_external=swapi_status,
    )
