import pytest
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from api.core.exceptions import DatabaseException
from api.domains.characters.repository import CharacterRepository
from api.domains.characters.models import Character

# Import related models to register them with SQLAlchemy
from api.domains.films.models import Film  # noqa: F401
from api.domains.starships.models import Starship  # noqa: F401


@pytest.fixture
def mock_session(mocker):
    """Mock async session."""
    session = mocker.AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create CharacterRepository with mocked session."""
    return CharacterRepository(mock_session)


@pytest.fixture
def sample_character(mocker):
    """Sample character for testing."""
    character = mocker.MagicMock(spec=Character)
    character.id = 1
    character.name = "Luke Skywalker"
    character.height = "172"
    character.mass = "77"
    character.hair_color = "blond"
    character.skin_color = "fair"
    character.eye_color = "blue"
    character.birth_year = "19BBY"
    character.gender = "male"
    character.created = datetime.now()
    character.edited = datetime.now()
    character.url = "https://api.example.com/people/1/"
    character.films = []
    character.starships = []
    return character


class TestCharacterRepository:
    """Test cases for CharacterRepository."""

    @pytest.mark.asyncio
    async def test_get_all_success(self, mocker, repository, sample_character):
        """Test successful retrieval of all characters."""
        characters = [sample_character]

        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = characters

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        result = await repository.get_all(skip=0, limit=10)

        assert len(result) == 1
        assert result[0] == sample_character
        repository.session.execute.assert_called_once()

        # Verify pagination parameters in query
        call_args = repository.session.execute.call_args[0][0]
        query_str = str(call_args).lower()
        assert "offset" in query_str or "limit" in query_str

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, mocker, repository):
        """Test get_all with custom pagination parameters."""
        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = []

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        await repository.get_all(skip=20, limit=50)

        repository.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_database_error(self, repository):
        """Test database error handling in get_all."""
        repository.session.execute.side_effect = SQLAlchemyError("Query failed")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.get_all()

        assert "Failed to retrieve characters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_name_success(self, mocker, repository, sample_character):
        """Test successful retrieval by name."""
        characters = [sample_character]

        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = characters

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        result = await repository.get_by_name("Luke Skywalker")

        assert len(result) == 1
        assert result[0] == sample_character
        repository.session.execute.assert_called_once()

        # Verify the query includes name filter and pagination
        call_args = repository.session.execute.call_args[0][0]
        query_str = str(call_args).lower()
        assert "ilike" in query_str or "like lower(" in query_str
        assert "offset" in query_str or "limit" in query_str

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, mocker, repository):
        """Test retrieval by name when character doesn't exist."""
        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = []

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        result = await repository.get_by_name("Non-existent Character")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_name_database_error(self, repository):
        """Test database error handling in get_by_name."""
        repository.session.execute.side_effect = SQLAlchemyError("Connection lost")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.get_by_name("Luke Skywalker")

        assert "Failed to retrieve character by name 'Luke Skywalker'" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_get_by_url_success(self, mocker, repository, sample_character):
        """Test successful retrieval by URL."""
        mock_result = mocker.MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_character
        repository.session.execute.return_value = mock_result

        result = await repository.get_by_url("https://api.example.com/people/1/")

        assert result == sample_character
        repository.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_url_not_found(self, mocker, repository):
        """Test retrieval by URL when character doesn't exist."""
        mock_result = mocker.MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        repository.session.execute.return_value = mock_result

        result = await repository.get_by_url("https://api.example.com/people/999/")

        assert result is None
        repository.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_url_database_error(self, repository):
        """Test database error handling in get_by_url."""
        test_url = "https://api.example.com/people/1/"
        repository.session.execute.side_effect = SQLAlchemyError("Query timeout")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.get_by_url(test_url)

        assert f"Failed to retrieve character by URL '{test_url}'" in str(
            exc_info.value
        )

    @pytest.mark.asyncio
    async def test_update_success(self, repository, sample_character):
        """Test successful character update."""
        # Mock successful commit and refresh
        repository.session.commit.return_value = None
        repository.session.refresh.return_value = None

        result = await repository.update(sample_character)

        assert result == sample_character
        repository.session.commit.assert_called_once()
        repository.session.refresh.assert_called_once_with(sample_character)

    @pytest.mark.asyncio
    async def test_update_database_error(self, repository, sample_character):
        """Test database error handling in update."""
        repository.session.commit.side_effect = SQLAlchemyError("Constraint violation")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.update(sample_character)

        assert "Failed to update character" in str(exc_info.value)
        repository.session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_inheritance_from_base_repository(self, repository):
        """Test that CharacterRepository properly inherits from BaseRepository."""
        from api.core.base_repository import BaseRepository

        assert isinstance(repository, BaseRepository)
        assert hasattr(repository, "session")

    def test_get_count_query_without_name(self, repository):
        """Test get_count_query without name filter."""
        query = repository.get_count_query()

        query_str = str(query).lower()
        assert "select" in query_str
        assert "character" in query_str
        assert "ilike" not in query_str

    def test_get_count_query_with_name(self, repository):
        """Test get_count_query with name filter."""
        query = repository.get_count_query(name="Luke")

        query_str = str(query).lower()
        assert "select" in query_str
        assert "character" in query_str
        assert "ilike" in query_str or "like lower(" in query_str
