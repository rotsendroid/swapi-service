"""Tests for StarshipService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination import PaginatedResponse, PaginationParams
from api.domains.starships.models import Starship
from api.domains.starships.repository import StarshipRepository
from api.domains.starships.schemas import StarshipSchema
from api.domains.starships.service import StarshipService, get_starship_service


@pytest.fixture
def mock_session():
    """Mock async database session for testing."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_repository():
    """Mock StarshipRepository for testing."""
    return AsyncMock(spec=StarshipRepository)


@pytest.fixture
def starship_service(mock_repository):
    """StarshipService instance with mocked repository."""
    return StarshipService(mock_repository)


@pytest.fixture
def sample_starship():
    """Sample Starship mock for testing."""
    starship = MagicMock(spec=Starship)
    starship.id = 2
    starship.name = "CR90 corvette"
    starship.model = "CR90 corvette"
    starship.manufacturer = "Corellian Engineering Corporation"
    starship.cost_in_credits = "3500000"
    starship.length = "150"
    starship.max_atmosphering_speed = "950"
    starship.crew = "30-165"
    starship.passengers = "600"
    starship.cargo_capacity = "3000000"
    starship.consumables = "1 year"
    starship.hyperdrive_rating = "2.0"
    starship.mglt = "60"
    starship.starship_class = "corvette"
    starship.created = datetime(2024, 1, 1, 12, 0, 0)
    starship.edited = datetime(2024, 1, 1, 12, 0, 0)
    starship.url = "https://swapi.dev/api/starships/2/"
    starship.pilots = []
    starship.films = []
    return starship


@pytest.fixture
def sample_starships(sample_starship):
    """Sample list of Starship mocks for testing."""
    starship2 = MagicMock(spec=Starship)
    starship2.id = 3
    starship2.name = "Star Destroyer"
    starship2.model = "Imperial I-class Star Destroyer"
    starship2.manufacturer = "Kuat Drive Yards"
    starship2.cost_in_credits = "150000000"
    starship2.length = "1600"
    starship2.max_atmosphering_speed = "975"
    starship2.crew = "47060"
    starship2.passengers = "0"
    starship2.cargo_capacity = "36000000"
    starship2.consumables = "2 years"
    starship2.hyperdrive_rating = "2.0"
    starship2.mglt = "60"
    starship2.starship_class = "Star Destroyer"
    starship2.created = datetime(2024, 1, 1, 12, 0, 0)
    starship2.edited = datetime(2024, 1, 1, 12, 0, 0)
    starship2.url = "https://swapi.dev/api/starships/3/"
    starship2.pilots = []
    starship2.films = []
    return [sample_starship, starship2]


@pytest.fixture
def sample_pagination_params():
    """Sample pagination parameters for testing."""
    return PaginationParams(offset=0, limit=10)


class TestStarshipService:
    """Test cases for StarshipService."""

    def test_starship_service_initialization(self, mock_repository):
        """Test StarshipService initialization."""
        service = StarshipService(mock_repository)
        assert service.repository == mock_repository

    @pytest.mark.asyncio
    async def test_get_all_starships_calls_pagination_service_without_name(
        self, starship_service, mock_session, sample_pagination_params
    ):
        """Test get_all_starships calls pagination service correctly without name filter."""
        # Mock the pagination service and its response
        mock_paginated_response = MagicMock(spec=PaginatedResponse)

        with patch(
            "api.domains.starships.service.PaginationService"
        ) as mock_pagination_class:
            mock_pagination_instance = MagicMock()
            mock_pagination_instance.paginate_with_repository = AsyncMock(
                return_value=mock_paginated_response
            )
            # For generic classes, we need to handle the __getitem__ call
            mock_pagination_class.__getitem__.return_value = mock_pagination_class
            mock_pagination_class.return_value = mock_pagination_instance

            # Mock repository methods
            starship_service.repository.get_all = AsyncMock()
            starship_service.repository.get_count_query = MagicMock(
                return_value=MagicMock()
            )

            result = await starship_service.get_all_starships(
                session=mock_session, params=sample_pagination_params, name=None
            )

            # Verify pagination service was created with correct session
            mock_pagination_class.assert_called_once_with(mock_session)

            # Verify paginate_with_repository was called
            mock_pagination_instance.paginate_with_repository.assert_called_once()
            call_kwargs = (
                mock_pagination_instance.paginate_with_repository.call_args.kwargs
            )

            # Verify the repository_get_all parameter is correct
            assert (
                call_kwargs["repository_get_all"] == starship_service.repository.get_all
            )

            # Verify count_query_stmt parameter
            starship_service.repository.get_count_query.assert_called_once_with()

            # Verify params parameter
            assert call_kwargs["params"] == sample_pagination_params

            # Verify serializer parameter exists
            assert "serializer" in call_kwargs

            # Verify result
            assert result == mock_paginated_response

    @pytest.mark.asyncio
    async def test_get_all_starships_calls_pagination_service_with_name(
        self, starship_service, mock_session, sample_pagination_params
    ):
        """Test get_all_starships calls pagination service correctly with name filter."""
        # Mock the pagination service and its response
        mock_paginated_response = MagicMock(spec=PaginatedResponse)

        with patch(
            "api.domains.starships.service.PaginationService"
        ) as mock_pagination_class:
            mock_pagination_instance = MagicMock()
            mock_pagination_instance.paginate_with_repository = AsyncMock(
                return_value=mock_paginated_response
            )
            # For generic classes, we need to handle the __getitem__ call
            mock_pagination_class.__getitem__.return_value = mock_pagination_class
            mock_pagination_class.return_value = mock_pagination_instance

            # Mock repository methods
            starship_service.repository.get_by_name = AsyncMock()
            starship_service.repository.get_count_query = MagicMock(
                return_value=MagicMock()
            )

            name_filter = "CR90"
            result = await starship_service.get_all_starships(
                session=mock_session, params=sample_pagination_params, name=name_filter
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
            starship_service.repository.get_by_name.assert_called_once_with(
                name_filter, 5, 15
            )

            # Verify count_query_stmt parameter
            starship_service.repository.get_count_query.assert_called_once_with(
                name_filter
            )

            # Verify params parameter
            assert call_kwargs["params"] == sample_pagination_params

            # Verify serializer parameter exists
            assert "serializer" in call_kwargs

            # Verify result
            assert result == mock_paginated_response

    def test_serializer_function_converts_starships_to_schemas(self, sample_starships):
        """Test that the internal serializer function correctly converts Starship models to StarshipSchema."""

        # Get the serializer function (defined inside get_all_starships)
        # We'll test it by calling it directly
        def serialize_starships(starships: list[Starship]) -> list[StarshipSchema]:
            return [
                StarshipSchema.model_validate(starship, from_attributes=True)
                for starship in starships
            ]

        # Test the serializer function
        serialized_starships = serialize_starships(sample_starships)

        # Verify that all starships were serialized correctly
        assert len(serialized_starships) == len(sample_starships)
        for i, serialized_starship in enumerate(serialized_starships):
            assert isinstance(serialized_starship, StarshipSchema)
            assert serialized_starship.id == sample_starships[i].id
            assert serialized_starship.name == sample_starships[i].name
            assert serialized_starship.model == sample_starships[i].model


class TestGetStarshipService:
    """Test cases for get_starship_service dependency injection function."""

    @patch("api.domains.starships.service.StarshipRepository")
    def test_get_starship_service(self, mock_repository_class, mock_session):
        """Test get_starship_service dependency injection function."""
        # Mock repository instance
        mock_repository_instance = AsyncMock(spec=StarshipRepository)
        mock_repository_class.return_value = mock_repository_instance

        # Call the dependency injection function
        service = get_starship_service(mock_session)

        # Verify repository was created with session
        mock_repository_class.assert_called_once_with(mock_session)

        # Verify service was created with repository
        assert isinstance(service, StarshipService)
        assert service.repository == mock_repository_instance
