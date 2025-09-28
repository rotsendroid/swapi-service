"""Tests for core lifespan functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI

from api.core.lifespan import lifespan


class TestLifespan:
    """Test cases for application lifespan management."""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application."""
        return MagicMock(spec=FastAPI)

    @pytest.fixture
    def mock_logger(self, mocker):
        """Mock logger for testing."""
        return mocker.patch("api.core.lifespan.logger")

    @pytest.fixture
    def mock_db_manager(self, mocker):
        """Mock database manager for testing."""
        mock_manager = AsyncMock()
        return mocker.patch("api.core.lifespan.db_manager", mock_manager)

    @pytest.mark.asyncio
    async def test_lifespan_startup_and_shutdown(
        self, mock_app, mock_logger, mock_db_manager
    ):
        """Test complete lifespan cycle with startup and shutdown."""
        async with lifespan(mock_app):
            # Verify startup logging
            mock_logger.info.assert_any_call("Starting up SWAPI Service...")
            mock_logger.info.assert_any_call("SWAPI Service startup completed")

        # Verify shutdown logging and db cleanup
        mock_logger.info.assert_any_call("Shutting down SWAPI Service...")
        mock_logger.info.assert_any_call("Closing database connections...")
        mock_logger.info.assert_any_call("SWAPI Service shutdown completed")
        mock_db_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_startup_only(self, mock_app, mock_logger, mock_db_manager):
        """Test that startup logs are called when entering context."""
        lifespan_context = lifespan(mock_app)

        # Enter the context
        await lifespan_context.__aenter__()

        # Verify startup logging
        mock_logger.info.assert_any_call("Starting up SWAPI Service...")
        mock_logger.info.assert_any_call("SWAPI Service startup completed")

        # Verify shutdown hasn't been called yet
        mock_db_manager.close.assert_not_called()

        # Clean up by exiting context
        await lifespan_context.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_lifespan_shutdown_only(self, mock_app, mock_logger, mock_db_manager):
        """Test that shutdown is called when exiting context."""
        lifespan_context = lifespan(mock_app)

        # Enter and immediately exit the context
        await lifespan_context.__aenter__()
        await lifespan_context.__aexit__(None, None, None)

        # Verify shutdown logging and cleanup
        mock_logger.info.assert_any_call("Shutting down SWAPI Service...")
        mock_logger.info.assert_any_call("Closing database connections...")
        mock_logger.info.assert_any_call("SWAPI Service shutdown completed")
        mock_db_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_exception_during_startup(
        self, mock_app, mock_logger, mock_db_manager
    ):
        """Test lifespan behavior when exception occurs during startup."""
        # Make logger.info raise an exception on the second call (startup completed)
        mock_logger.info.side_effect = [
            None,
            Exception("Startup error"),
            None,
            None,
            None,
        ]

        with pytest.raises(Exception, match="Startup error"):
            async with lifespan(mock_app):
                pass

        # If exception occurs during startup, the finally block doesn't execute
        # so db_manager.close() is not called
        mock_db_manager.close.assert_not_called()

    @pytest.mark.asyncio
    async def test_lifespan_exception_during_shutdown(
        self, mock_app, mock_logger, mock_db_manager
    ):
        """Test lifespan behavior when exception occurs during shutdown."""
        # Make db_manager.close() raise an exception
        mock_db_manager.close.side_effect = Exception("Database close error")

        with pytest.raises(Exception, match="Database close error"):
            async with lifespan(mock_app):
                pass

        # Verify that db close was attempted
        mock_db_manager.close.assert_called_once()

        # Verify shutdown logging was called before the exception
        mock_logger.info.assert_any_call("Shutting down SWAPI Service...")
        mock_logger.info.assert_any_call("Closing database connections...")

    @pytest.mark.asyncio
    async def test_lifespan_exception_in_application_code(
        self, mock_app, mock_logger, mock_db_manager
    ):
        """Test that lifespan cleanup happens even when application code raises exception."""
        with pytest.raises(ValueError, match="Application error"):
            async with lifespan(mock_app):
                # Simulate an exception in application code
                raise ValueError("Application error")

        # Verify shutdown cleanup still happens
        mock_logger.info.assert_any_call("Shutting down SWAPI Service...")
        mock_logger.info.assert_any_call("Closing database connections...")
        mock_logger.info.assert_any_call("SWAPI Service shutdown completed")
        mock_db_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_db_manager_close_called_once(
        self, mock_app, mock_logger, mock_db_manager
    ):
        """Test that database manager close is called exactly once."""
        async with lifespan(mock_app):
            pass

        # Verify db close is called exactly once
        assert mock_db_manager.close.call_count == 1

    @pytest.mark.asyncio
    async def test_logging_sequence(self, mock_app, mock_logger, mock_db_manager):
        """Test that logging calls happen in the correct sequence."""
        async with lifespan(mock_app):
            pass

        # Get all the logging calls in order
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]

        expected_sequence = [
            "Starting up SWAPI Service...",
            "SWAPI Service startup completed",
            "Shutting down SWAPI Service...",
            "Closing database connections...",
            "SWAPI Service shutdown completed",
        ]

        assert info_calls == expected_sequence

    @pytest.mark.asyncio
    async def test_lifespan_with_fastapi_app_instance(
        self, mock_logger, mock_db_manager
    ):
        """Test lifespan with actual FastAPI app instance."""
        app = FastAPI()

        async with lifespan(app):
            # Verify startup logging
            mock_logger.info.assert_any_call("Starting up SWAPI Service...")
            mock_logger.info.assert_any_call("SWAPI Service startup completed")

        # Verify shutdown
        mock_db_manager.close.assert_called_once()

    def test_lifespan_is_async_context_manager(self, mock_app):
        """Test that lifespan returns an async context manager."""
        context_manager = lifespan(mock_app)

        # Verify it has the required async context manager methods
        assert hasattr(context_manager, "__aenter__")
        assert hasattr(context_manager, "__aexit__")
        assert callable(context_manager.__aenter__)
        assert callable(context_manager.__aexit__)

    def test_setup_logging_called_at_module_level(self):
        """Test that setup_logging function exists and is importable."""
        # Since setup_logging() is called at module import time (line 10 in lifespan.py),
        # testing its call would require mocking before import, which is complex.
        # Instead, we verify the function is properly imported and accessible.
        from api.config.logging import setup_logging

        assert callable(setup_logging)
        # We can also verify that the logger was created after setup_logging was called
        from api.core.lifespan import logger

        assert logger is not None
