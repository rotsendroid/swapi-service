"""Tests for BaseRepository functionality."""

from api.core.base_repository import BaseRepository


class TestBaseRepository:
    """Test cases for BaseRepository."""

    def test_extract_id_from_url(self, mocker):
        """Test URL ID extraction functionality."""

        # Create a concrete implementation for testing
        class ConcreteRepository(BaseRepository):
            async def get_by_id(self, id: int):
                pass

            async def get_all(self, skip: int = 0, limit: int = 100):
                pass

            async def update(self, obj):
                pass

            async def get_by_url(self, url: str):
                pass

        mock_session = mocker.AsyncMock()
        repo = ConcreteRepository(mock_session)

        # Mock the utility function
        mock_extract = mocker.patch(
            "api.core.base_repository.extract_id_from_url", return_value=42
        )

        result = repo._extract_id_from_url("https://swapi.dev/api/people/42/")

        assert result == 42
        mock_extract.assert_called_once_with("https://swapi.dev/api/people/42/")

    def test_session_assignment(self, mocker):
        """Test that session is properly assigned."""

        class ConcreteRepository(BaseRepository):
            async def get_by_id(self, id: int):
                pass

            async def get_all(self, skip: int = 0, limit: int = 100):
                pass

            async def update(self, obj):
                pass

            async def get_by_url(self, url: str):
                pass

        mock_session = mocker.AsyncMock()
        repo = ConcreteRepository(mock_session)

        assert repo.session == mock_session
