"""Tests for postgres storage module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from api.storage.postgres import Base, DatabaseManager, db_manager, get_db_session


class TestBase:
    """Test cases for Base declarative base class."""

    def test_base_is_declarative_base(self):
        """Test that Base is a proper DeclarativeBase."""
        assert issubclass(Base, DeclarativeBase)

    def test_base_has_async_attrs(self):
        """Test that Base includes AsyncAttrs mixin."""
        # Check if Base has async attributes from AsyncAttrs
        # AsyncAttrs provides async lazy loading capabilities
        from sqlalchemy.ext.asyncio import AsyncAttrs

        assert issubclass(Base, AsyncAttrs)


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def test_database_manager_initialization(self, mock_settings):
        """Test DatabaseManager initialization."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            manager = DatabaseManager()
            assert manager.settings == mock_settings
            assert manager._engine is None
            assert manager._session_maker is None

    def test_create_engine_development_environment(self, mock_settings):
        """Test engine creation for development environment."""
        mock_settings.environment = "development"
        mock_settings.postgres_url = "postgresql+asyncpg://test:test@localhost/test_db"

        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            with patch(
                "api.storage.postgres.create_async_engine"
            ) as mock_create_engine:
                manager = DatabaseManager()
                manager._create_engine()

                mock_create_engine.assert_called_once_with(
                    mock_settings.postgres_url,
                    poolclass=NullPool,
                    echo=False,
                )

    def test_create_engine_testing_environment(self, mock_settings):
        """Test engine creation for testing environment."""
        mock_settings.environment = "testing"
        mock_settings.postgres_url = "postgresql+asyncpg://test:test@localhost/test_db"

        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            with patch(
                "api.storage.postgres.create_async_engine"
            ) as mock_create_engine:
                manager = DatabaseManager()
                manager._create_engine()

                mock_create_engine.assert_called_once_with(
                    mock_settings.postgres_url,
                    poolclass=NullPool,
                    echo=False,
                )

    def test_create_engine_production_environment(self, mock_settings):
        """Test engine creation for production environment."""
        mock_settings.environment = "production"
        mock_settings.postgres_url = "postgresql+asyncpg://user:pass@localhost/prod_db"

        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            with patch(
                "api.storage.postgres.create_async_engine"
            ) as mock_create_engine:
                manager = DatabaseManager()
                manager._create_engine()

                mock_create_engine.assert_called_once_with(
                    mock_settings.postgres_url,
                    poolclass=AsyncAdaptedQueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_timeout=30,
                    pool_recycle=3600,
                    pool_pre_ping=True,
                    echo=False,
                )

    def test_engine_property_lazy_initialization(self, mock_settings):
        """Test that engine property creates engine only when accessed."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            with patch(
                "api.storage.postgres.create_async_engine"
            ) as mock_create_engine:
                mock_engine = MagicMock()
                mock_create_engine.return_value = mock_engine

                manager = DatabaseManager()
                assert manager._engine is None

                # First access should create the engine
                engine = manager.engine
                assert engine == mock_engine
                assert manager._engine == mock_engine
                mock_create_engine.assert_called_once()

                # Second access should return cached engine
                engine2 = manager.engine
                assert engine2 == mock_engine
                assert mock_create_engine.call_count == 1

    def test_session_maker_property_lazy_initialization(self, mock_settings):
        """Test that session_maker property creates session maker only when accessed."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            with patch("api.storage.postgres.async_sessionmaker") as mock_sessionmaker:
                with patch.object(
                    DatabaseManager, "engine", new_callable=lambda: MagicMock()
                ):
                    mock_session_maker = MagicMock()
                    mock_sessionmaker.return_value = mock_session_maker

                    manager = DatabaseManager()
                    assert manager._session_maker is None

                    # First access should create the session maker
                    session_maker = manager.session_maker
                    assert session_maker == mock_session_maker
                    assert manager._session_maker == mock_session_maker

                    mock_sessionmaker.assert_called_once_with(
                        bind=manager.engine,
                        class_=AsyncSession,
                        expire_on_commit=False,
                        autoflush=True,
                        autocommit=False,
                    )

                    # Second access should return cached session maker
                    session_maker2 = manager.session_maker
                    assert session_maker2 == mock_session_maker
                    assert mock_sessionmaker.call_count == 1

    async def test_get_session_success(self, mock_settings):
        """Test successful session creation and cleanup."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            mock_session = AsyncMock(spec=AsyncSession)
            manager = DatabaseManager()

            # Mock the _session_maker attribute directly
            mock_session_maker = MagicMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_session_maker.return_value = mock_cm
            manager._session_maker = mock_session_maker

            async with manager.get_session() as session:
                assert session == mock_session

            # Verify session lifecycle
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()

    async def test_get_session_with_exception(self, mock_settings):
        """Test session rollback on exception."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            mock_session = AsyncMock(spec=AsyncSession)
            manager = DatabaseManager()

            # Mock the _session_maker attribute directly
            mock_session_maker = MagicMock()
            mock_cm = AsyncMock()
            mock_cm.__aenter__.return_value = mock_session
            mock_cm.__aexit__.return_value = None
            mock_session_maker.return_value = mock_cm
            manager._session_maker = mock_session_maker

            with pytest.raises(ValueError, match="Test exception"):
                async with manager.get_session() as session:
                    assert session == mock_session
                    raise ValueError("Test exception")

            # Verify session lifecycle with exception
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()

    async def test_close_with_engine(self, mock_settings):
        """Test closing database manager with existing engine."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            mock_engine = AsyncMock()
            manager = DatabaseManager()
            manager._engine = mock_engine
            manager._session_maker = MagicMock()

            await manager.close()

            mock_engine.dispose.assert_called_once()
            assert manager._engine is None
            assert manager._session_maker is None

    async def test_close_without_engine(self, mock_settings):
        """Test closing database manager without existing engine."""
        with patch("api.storage.postgres.get_settings", return_value=mock_settings):
            manager = DatabaseManager()
            assert manager._engine is None

            # Should not raise exception
            await manager.close()

            assert manager._engine is None
            assert manager._session_maker is None


class TestGlobalDatabaseManager:
    """Test cases for global database manager instance."""

    def test_db_manager_is_database_manager_instance(self):
        """Test that db_manager is an instance of DatabaseManager."""
        assert isinstance(db_manager, DatabaseManager)


class TestGetDbSession:
    """Test cases for get_db_session dependency function."""

    async def test_get_db_session_success(self):
        """Test successful database session dependency."""
        mock_session = AsyncMock(spec=AsyncSession)

        with patch.object(db_manager, "get_session") as mock_get_session:
            # Mock the async context manager properly
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_context

            # Test the async generator
            gen = get_db_session()
            session = await gen.__anext__()
            assert session == mock_session

            # Clean up generator
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_get_session.assert_called_once()

    async def test_get_db_session_exception_propagation(self):
        """Test that exceptions in get_db_session are properly propagated."""
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_get_session.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception, match="Database connection failed"):
                gen = get_db_session()
                await gen.__anext__()

    async def test_get_db_session_integration_with_db_manager(self):
        """Test that get_db_session properly integrates with db_manager."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock the get_session method directly instead of session_maker property
        with patch.object(db_manager, "get_session") as mock_get_session:
            mock_session_context = AsyncMock()
            mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_context.__aexit__ = AsyncMock(return_value=None)
            mock_get_session.return_value = mock_session_context

            # Test the generator
            gen = get_db_session()
            session = await gen.__anext__()
            assert session == mock_session

            # Clean up generator
            try:
                await gen.__anext__()
            except StopAsyncIteration:
                pass

            mock_get_session.assert_called_once()
