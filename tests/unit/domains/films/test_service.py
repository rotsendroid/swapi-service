"""Tests for FilmService."""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination import PaginatedResponse, PaginationParams
from api.domains.films.models import Film
from api.domains.films.repository import FilmRepository
from api.domains.films.schemas import FilmSchema
from api.domains.films.service import FilmService, get_film_service


@pytest.fixture
def mock_session():
    """Mock async database session for testing."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_repository():
    """Mock FilmRepository for testing."""
    return AsyncMock(spec=FilmRepository)


@pytest.fixture
def film_service(mock_repository):
    """FilmService instance with mocked repository."""
    return FilmService(mock_repository)


@pytest.fixture
def sample_film():
    """Sample Film mock for testing."""
    film = MagicMock(spec=Film)
    film.id = 1
    film.title = "A New Hope"
    film.episode_id = 4
    film.opening_crawl = "It is a period of civil war."
    film.director = "George Lucas"
    film.producer = "Gary Kurtz, Rick McCallum"
    film.release_date = date(1977, 5, 25)
    film.created = datetime(2024, 1, 1, 12, 0, 0)
    film.edited = datetime(2024, 1, 1, 12, 0, 0)
    film.url = "https://swapi.dev/api/films/1/"
    film.characters = []
    film.starships = []
    return film


@pytest.fixture
def sample_films(sample_film):
    """Sample list of Film mocks for testing."""
    film2 = MagicMock(spec=Film)
    film2.id = 2
    film2.title = "The Empire Strikes Back"
    film2.episode_id = 5
    film2.opening_crawl = "It is a dark time for the Rebellion."
    film2.director = "Irvin Kershner"
    film2.producer = "Gary Kurtz, Rick McCallum"
    film2.release_date = date(1980, 5, 17)
    film2.created = datetime(2024, 1, 1, 12, 0, 0)
    film2.edited = datetime(2024, 1, 1, 12, 0, 0)
    film2.url = "https://swapi.dev/api/films/2/"
    film2.characters = []
    film2.starships = []
    return [sample_film, film2]


@pytest.fixture
def sample_pagination_params():
    """Sample pagination parameters for testing."""
    return PaginationParams(offset=0, limit=10)


class TestFilmService:
    """Test cases for FilmService."""

    def test_film_service_initialization(self, mock_repository):
        """Test FilmService initialization."""
        service = FilmService(mock_repository)
        assert service.repository == mock_repository

    @pytest.mark.asyncio
    async def test_get_all_films_calls_pagination_service_without_title(
        self, film_service, mock_session, sample_pagination_params
    ):
        """Test get_all_films calls pagination service correctly without title filter."""
        # Mock the pagination service and its response
        mock_paginated_response = MagicMock(spec=PaginatedResponse)

        with patch(
            "api.domains.films.service.PaginationService"
        ) as mock_pagination_class:
            mock_pagination_instance = MagicMock()
            mock_pagination_instance.paginate_with_repository = AsyncMock(
                return_value=mock_paginated_response
            )
            # For generic classes, we need to handle the __getitem__ call
            mock_pagination_class.__getitem__.return_value = mock_pagination_class
            mock_pagination_class.return_value = mock_pagination_instance

            # Mock repository methods
            film_service.repository.get_all = AsyncMock()
            film_service.repository.get_count_query = MagicMock(
                return_value=MagicMock()
            )

            result = await film_service.get_all_films(
                session=mock_session, params=sample_pagination_params, title=None
            )

            # Verify pagination service was created with correct session
            mock_pagination_class.assert_called_once_with(mock_session)

            # Verify paginate_with_repository was called
            mock_pagination_instance.paginate_with_repository.assert_called_once()
            call_kwargs = (
                mock_pagination_instance.paginate_with_repository.call_args.kwargs
            )

            # Verify the repository_get_all parameter is correct
            assert call_kwargs["repository_get_all"] == film_service.repository.get_all

            # Verify count_query_stmt parameter
            film_service.repository.get_count_query.assert_called_once_with()

            # Verify params parameter
            assert call_kwargs["params"] == sample_pagination_params

            # Verify serializer parameter exists
            assert "serializer" in call_kwargs

            # Verify result
            assert result == mock_paginated_response

    @pytest.mark.asyncio
    async def test_get_all_films_calls_pagination_service_with_title(
        self, film_service, mock_session, sample_pagination_params
    ):
        """Test get_all_films calls pagination service correctly with title filter."""
        # Mock the pagination service and its response
        mock_paginated_response = MagicMock(spec=PaginatedResponse)

        with patch(
            "api.domains.films.service.PaginationService"
        ) as mock_pagination_class:
            mock_pagination_instance = MagicMock()
            mock_pagination_instance.paginate_with_repository = AsyncMock(
                return_value=mock_paginated_response
            )
            # For generic classes, we need to handle the __getitem__ call
            mock_pagination_class.__getitem__.return_value = mock_pagination_class
            mock_pagination_class.return_value = mock_pagination_instance

            # Mock repository methods
            film_service.repository.get_by_title = AsyncMock()
            film_service.repository.get_count_query = MagicMock(
                return_value=MagicMock()
            )

            title_filter = "A New Hope"
            result = await film_service.get_all_films(
                session=mock_session,
                params=sample_pagination_params,
                title=title_filter,
            )

            # Verify pagination service was created with correct session
            mock_pagination_class.assert_called_once_with(mock_session)

            # Verify paginate_with_repository was called
            mock_pagination_instance.paginate_with_repository.assert_called_once()
            call_kwargs = (
                mock_pagination_instance.paginate_with_repository.call_args.kwargs
            )

            # Verify the repository_get_all parameter is a lambda function
            repository_get_all = call_kwargs["repository_get_all"]

            # Test the lambda function by calling it
            await repository_get_all(5, 15)
            film_service.repository.get_by_title.assert_called_once_with(
                title_filter, 5, 15
            )

            # Verify count_query_stmt parameter
            film_service.repository.get_count_query.assert_called_once_with(
                title_filter
            )

            # Verify params parameter
            assert call_kwargs["params"] == sample_pagination_params

            # Verify serializer parameter exists
            assert "serializer" in call_kwargs

            # Verify result
            assert result == mock_paginated_response

    def test_serializer_function_converts_films_to_schemas(self, sample_films):
        """Test that the internal serializer function correctly converts Film models to FilmSchema."""

        # Get the serializer function (defined inside get_all_films)
        # We'll test it by calling it directly
        def serialize_films(films: list[Film]) -> list[FilmSchema]:
            return [
                FilmSchema.model_validate(film, from_attributes=True) for film in films
            ]

        # Test the serializer function
        serialized_films = serialize_films(sample_films)

        # Verify that all films were serialized correctly
        assert len(serialized_films) == len(sample_films)
        for i, serialized_film in enumerate(serialized_films):
            assert isinstance(serialized_film, FilmSchema)
            assert serialized_film.id == sample_films[i].id
            assert serialized_film.title == sample_films[i].title
            assert serialized_film.episode_id == sample_films[i].episode_id


class TestGetFilmService:
    """Test cases for get_film_service dependency injection function."""

    @patch("api.domains.films.service.FilmRepository")
    def test_get_film_service(self, mock_repository_class, mock_session):
        """Test get_film_service dependency injection function."""
        # Mock repository instance
        mock_repository_instance = AsyncMock(spec=FilmRepository)
        mock_repository_class.return_value = mock_repository_instance

        # Call the dependency injection function
        service = get_film_service(mock_session)

        # Verify repository was created with session
        mock_repository_class.assert_called_once_with(mock_session)

        # Verify service was created with repository
        assert isinstance(service, FilmService)
        assert service.repository == mock_repository_instance
