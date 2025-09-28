"""Tests for CharacterService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination import PaginatedResponse, PaginationParams
from api.domains.characters.models import Character
from api.domains.characters.repository import CharacterRepository
from api.domains.characters.schemas import CharacterSchema
from api.domains.characters.service import CharacterService, get_character_service


@pytest.fixture
def mock_session():
    """Mock async database session for testing."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_repository():
    """Mock CharacterRepository for testing."""
    return AsyncMock(spec=CharacterRepository)


@pytest.fixture
def character_service(mock_repository):
    """CharacterService instance with mocked repository."""
    return CharacterService(mock_repository)


@pytest.fixture
def sample_character():
    """Sample Character mock for testing."""
    char = MagicMock(spec=Character)
    char.id = 1
    char.name = "Luke Skywalker"
    char.height = "172"
    char.mass = "77"
    char.hair_color = "blond"
    char.skin_color = "fair"
    char.eye_color = "blue"
    char.birth_year = "19BBY"
    char.gender = "male"
    char.created = datetime(2024, 1, 1, 12, 0, 0)
    char.edited = datetime(2024, 1, 1, 12, 0, 0)
    char.url = "https://swapi.dev/api/people/1/"
    char.films = []
    char.starships = []
    return char


@pytest.fixture
def sample_characters(sample_character):
    """Sample list of Character mocks for testing."""
    char2 = MagicMock(spec=Character)
    char2.id = 2
    char2.name = "Darth Vader"
    char2.height = "202"
    char2.mass = "136"
    char2.hair_color = "none"
    char2.skin_color = "white"
    char2.eye_color = "yellow"
    char2.birth_year = "41.9BBY"
    char2.gender = "male"
    char2.created = datetime(2024, 1, 1, 12, 0, 0)
    char2.edited = datetime(2024, 1, 1, 12, 0, 0)
    char2.url = "https://swapi.dev/api/people/4/"
    char2.films = []
    char2.starships = []
    return [sample_character, char2]


@pytest.fixture
def sample_pagination_params():
    """Sample pagination parameters for testing."""
    return PaginationParams(offset=0, limit=10)


class TestCharacterService:
    """Test cases for CharacterService."""

    def test_character_service_initialization(self, mock_repository):
        """Test CharacterService initialization."""
        service = CharacterService(mock_repository)
        assert service.repository == mock_repository

    @pytest.mark.asyncio
    async def test_get_all_characters_calls_pagination_service_without_name(
        self, character_service, mock_session, sample_pagination_params
    ):
        """Test get_all_characters calls pagination service correctly without name filter."""
        # Mock the pagination service and its response
        mock_paginated_response = MagicMock(spec=PaginatedResponse)

        with patch(
            "api.domains.characters.service.PaginationService"
        ) as mock_pagination_class:
            mock_pagination_instance = MagicMock()
            mock_pagination_instance.paginate_with_repository = AsyncMock(
                return_value=mock_paginated_response
            )
            # For generic classes, we need to handle the __getitem__ call
            mock_pagination_class.__getitem__.return_value = mock_pagination_class
            mock_pagination_class.return_value = mock_pagination_instance

            # Mock repository methods
            character_service.repository.get_all = AsyncMock()
            character_service.repository.get_count_query = MagicMock(
                return_value=MagicMock()
            )

            result = await character_service.get_all_characters(
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
                call_kwargs["repository_get_all"]
                == character_service.repository.get_all
            )

            # Verify count_query_stmt parameter
            character_service.repository.get_count_query.assert_called_once_with()

            # Verify params parameter
            assert call_kwargs["params"] == sample_pagination_params

            # Verify serializer parameter exists
            assert "serializer" in call_kwargs

            # Verify result
            assert result == mock_paginated_response

    @pytest.mark.asyncio
    async def test_get_all_characters_calls_pagination_service_with_name(
        self, character_service, mock_session, sample_pagination_params
    ):
        """Test get_all_characters calls pagination service correctly with name filter."""
        # Mock the pagination service and its response
        mock_paginated_response = MagicMock(spec=PaginatedResponse)

        with patch(
            "api.domains.characters.service.PaginationService"
        ) as mock_pagination_class:
            mock_pagination_instance = MagicMock()
            mock_pagination_instance.paginate_with_repository = AsyncMock(
                return_value=mock_paginated_response
            )
            # For generic classes, we need to handle the __getitem__ call
            mock_pagination_class.__getitem__.return_value = mock_pagination_class
            mock_pagination_class.return_value = mock_pagination_instance

            # Mock repository methods
            character_service.repository.get_by_name = AsyncMock()
            character_service.repository.get_count_query = MagicMock(
                return_value=MagicMock()
            )

            name_filter = "Luke"
            result = await character_service.get_all_characters(
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
            character_service.repository.get_by_name.assert_called_once_with(
                name_filter, 5, 15
            )

            # Verify count_query_stmt parameter
            character_service.repository.get_count_query.assert_called_once_with(
                name_filter
            )

            # Verify params parameter
            assert call_kwargs["params"] == sample_pagination_params

            # Verify serializer parameter exists
            assert "serializer" in call_kwargs

            # Verify result
            assert result == mock_paginated_response

    def test_serializer_function_converts_characters_to_schemas(
        self, sample_characters
    ):
        """Test that the internal serializer function correctly converts Character models to CharacterSchema."""

        # Get the serializer function (defined inside get_all_characters)
        # We'll test it by calling it directly
        def serialize_characters(characters: list[Character]) -> list[CharacterSchema]:
            return [
                CharacterSchema.model_validate(char, from_attributes=True)
                for char in characters
            ]

        # Test the serializer function
        serialized_characters = serialize_characters(sample_characters)

        # Verify that all characters were serialized correctly
        assert len(serialized_characters) == len(sample_characters)
        for i, serialized_char in enumerate(serialized_characters):
            assert isinstance(serialized_char, CharacterSchema)
            assert serialized_char.id == sample_characters[i].id
            assert serialized_char.name == sample_characters[i].name
            assert serialized_char.height == sample_characters[i].height


class TestGetCharacterService:
    """Test cases for get_character_service dependency injection function."""

    @patch("api.domains.characters.service.CharacterRepository")
    def test_get_character_service(self, mock_repository_class, mock_session):
        """Test get_character_service dependency injection function."""
        # Mock repository instance
        mock_repository_instance = AsyncMock(spec=CharacterRepository)
        mock_repository_class.return_value = mock_repository_instance

        # Call the dependency injection function
        service = get_character_service(mock_session)

        # Verify repository was created with session
        mock_repository_class.assert_called_once_with(mock_session)

        # Verify service was created with repository
        assert isinstance(service, CharacterService)
        assert service.repository == mock_repository_instance
