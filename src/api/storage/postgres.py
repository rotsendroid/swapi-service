from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from api.config.settings import get_settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class DatabaseManager:
    def __init__(self):
        self.settings = get_settings()
        self._engine = None
        self._session_maker = None

    def _create_engine(self):
        """Create async engine with production-ready configuration."""
        if self.settings.environment == "testing":
            # Use NullPool for testing to avoid connection issues
            return create_async_engine(
                self.settings.postgres_url,
                poolclass=NullPool,
                echo=False,
            )
        else:
            # Production configuration with connection pooling
            return create_async_engine(
                self.settings.postgres_url,
                poolclass=AsyncAdaptedQueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,  # Recycle connections after 1 hour
                pool_pre_ping=True,  # Validate connections before use
                echo=False,  # Use unified logging instead
            )

    @property
    def engine(self):
        """Get or create the async engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_maker(self):
        """Get or create the session maker."""
        if self._session_maker is None:
            self._session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
        return self._session_maker

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session with proper cleanup."""
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self):
        """Close the database engine and all connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_maker = None


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for FastAPI to get database sessions."""
    async with db_manager.get_session() as session:
        yield session
