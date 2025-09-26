from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from api.config.logging import get_logger, setup_logging
from api.storage.postgres import db_manager

# Setup logging first, before creating any loggers
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for FastAPI application startup and shutdown."""
    logger.info("Starting up SWAPI Service...")

    logger.info("SWAPI Service startup completed")

    try:
        yield
    finally:
        logger.info("Shutting down SWAPI Service...")

        logger.info("Closing database connections...")
        await db_manager.close()

        logger.info("SWAPI Service shutdown completed")
