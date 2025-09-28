"""Shared test fixtures and configuration."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_db_session(mocker):
    """Mock async database session for testing."""
    session = mocker.AsyncMock(spec=AsyncSession)
    session.add = mocker.MagicMock()
    session.commit = mocker.AsyncMock()
    session.rollback = mocker.AsyncMock()
    session.refresh = mocker.AsyncMock()
    session.execute = mocker.AsyncMock()
    return session


@pytest.fixture
def mock_settings(mocker):
    """Mock application settings."""
    settings = mocker.MagicMock()
    settings.swapi_base_url = "https://swapi.dev/api"
    settings.postgres_url = "postgresql+asyncpg://test:test@localhost/test_db"
    settings.environment = "testing"
    return settings


@pytest.fixture
def sample_datetime():
    """Sample datetime for testing."""
    from datetime import datetime

    return datetime(2014, 12, 10, 14, 23, 31, 880000)


@pytest.fixture
def sample_urls():
    """Sample SWAPI URLs for testing."""
    return {
        "film": "https://swapi.dev/api/films/1/",
        "character": "https://swapi.dev/api/people/1/",
        "starship": "https://swapi.dev/api/starships/12/",
        "planet": "https://swapi.dev/api/planets/1/",
    }


def mock_aiohttp_session(mocker, mock_response):
    """Helper function to create a properly mocked aiohttp.ClientSession.

    This helper sets up the complex async context manager mocking required
    for testing code that uses aiohttp.ClientSession with nested async context managers:

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # test code here

    Args:
        mocker: pytest-mock mocker fixture
        mock_response: Mock response object with status, read(), etc.

    Returns:
        The patched aiohttp.ClientSession

    Example:
        mock_response = mocker.MagicMock()
        mock_response.status = 200
        mock_response.read = mocker.AsyncMock(return_value=b'{"data": "test"}')
        mock_aiohttp_session(mocker, mock_response)
    """
    mock_session = mocker.AsyncMock()
    mock_session.__aenter__.return_value = mock_session

    # Create a proper async context manager for session.get()
    mock_get_context = mocker.MagicMock()
    mock_get_context.__aenter__ = mocker.AsyncMock(return_value=mock_response)
    mock_get_context.__aexit__ = mocker.AsyncMock(return_value=None)

    # Make session.get a regular Mock, not an AsyncMock
    mock_session.get = mocker.Mock(return_value=mock_get_context)

    return mocker.patch("aiohttp.ClientSession", return_value=mock_session)
