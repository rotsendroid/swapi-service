import pytest
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from api.core.exceptions import DatabaseException
from api.domains.films.repository import FilmRepository
from api.domains.films.models import Film

# Import related models to register them with SQLAlchemy
from api.domains.characters.models import Character  # noqa: F401
from api.domains.starships.models import Starship  # noqa: F401


@pytest.fixture
def mock_session(mocker):
    """Mock async session."""
    session = mocker.AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create FilmRepository with mocked session."""
    return FilmRepository(mock_session)


@pytest.fixture
def sample_film(mocker):
    """Sample film for testing."""
    film = mocker.MagicMock(spec=Film)
    film.id = 1
    film.title = "A New Hope"
    film.episode_id = 4
    film.opening_crawl = "It is a period of civil war..."
    film.director = "George Lucas"
    film.producer = "Gary Kurtz, Rick McCallum"
    film.release_date = datetime(1977, 5, 25).date()
    film.created = datetime.now()
    film.edited = datetime.now()
    film.url = "https://api.example.com/films/1/"
    film.characters = []
    film.starships = []
    return film


class TestFilmRepository:
    """Test cases for FilmRepository."""

    @pytest.mark.asyncio
    async def test_get_all_success(self, mocker, repository, sample_film):
        """Test successful retrieval of all films."""
        films = [sample_film]

        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = films

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        result = await repository.get_all(skip=0, limit=10)

        assert len(result) == 1
        assert result[0] == sample_film
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

        assert "Failed to retrieve films" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_title_success(self, mocker, repository, sample_film):
        """Test successful retrieval by title."""
        films = [sample_film]

        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = films

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        result = await repository.get_by_title("A New Hope")

        assert len(result) == 1
        assert result[0] == sample_film
        repository.session.execute.assert_called_once()

        # Verify the query includes title filter and pagination
        call_args = repository.session.execute.call_args[0][0]
        query_str = str(call_args).lower()
        assert "ilike" in query_str or "like lower(" in query_str
        assert "offset" in query_str or "limit" in query_str

    @pytest.mark.asyncio
    async def test_get_by_title_not_found(self, mocker, repository):
        """Test retrieval by title when film doesn't exist."""
        mock_scalars = mocker.MagicMock()
        mock_scalars.all.return_value = []

        mock_result = mocker.MagicMock()
        mock_result.scalars.return_value = mock_scalars

        repository.session.execute.return_value = mock_result

        result = await repository.get_by_title("Non-existent Film")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_title_database_error(self, repository):
        """Test database error handling in get_by_title."""
        repository.session.execute.side_effect = SQLAlchemyError("Connection lost")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.get_by_title("A New Hope")

        assert "Failed to retrieve films by title 'A New Hope'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_by_url_success(self, mocker, repository, sample_film):
        """Test successful retrieval by URL."""
        mock_result = mocker.MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_film
        repository.session.execute.return_value = mock_result

        result = await repository.get_by_url("https://api.example.com/films/1/")

        assert result == sample_film
        repository.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_url_not_found(self, mocker, repository):
        """Test retrieval by URL when film doesn't exist."""
        mock_result = mocker.MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        repository.session.execute.return_value = mock_result

        result = await repository.get_by_url("https://api.example.com/films/999/")

        assert result is None
        repository.session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_url_database_error(self, repository):
        """Test database error handling in get_by_url."""
        test_url = "https://api.example.com/films/1/"
        repository.session.execute.side_effect = SQLAlchemyError("Query timeout")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.get_by_url(test_url)

        assert f"Failed to retrieve film by URL '{test_url}'" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_success(self, repository, sample_film):
        """Test successful film update."""
        # Mock successful commit and refresh
        repository.session.commit.return_value = None
        repository.session.refresh.return_value = None

        result = await repository.update(sample_film)

        assert result == sample_film
        repository.session.commit.assert_called_once()
        repository.session.refresh.assert_called_once_with(sample_film)

    @pytest.mark.asyncio
    async def test_update_database_error(self, repository, sample_film):
        """Test database error handling in update."""
        repository.session.commit.side_effect = SQLAlchemyError("Constraint violation")

        with pytest.raises(DatabaseException) as exc_info:
            await repository.update(sample_film)

        assert "Failed to update film" in str(exc_info.value)
        repository.session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_inheritance_from_base_repository(self, repository):
        """Test that FilmRepository properly inherits from BaseRepository."""
        from api.core.base_repository import BaseRepository

        assert isinstance(repository, BaseRepository)
        assert hasattr(repository, "session")

    def test_get_count_query_without_title(self, repository):
        """Test get_count_query without title filter."""
        query = repository.get_count_query()

        query_str = str(query).lower()
        assert "select" in query_str
        assert "film" in query_str
        assert "ilike" not in query_str

    def test_get_count_query_with_title(self, repository):
        """Test get_count_query with title filter."""
        query = repository.get_count_query(title="Hope")

        query_str = str(query).lower()
        assert "select" in query_str
        assert "film" in query_str
        assert "ilike" in query_str or "like lower(" in query_str
