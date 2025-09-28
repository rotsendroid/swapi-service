import aiohttp
import orjson
import pytest
from sqlalchemy.exc import SQLAlchemyError

from api.core.exceptions import (
    DatabaseException,
    ExternalServiceException,
    InputValidationException,
    InternalServerException,
)
from tests.conftest import mock_aiohttp_session
from api.core.populatedb.schemas import (
    CharacterInputSchema,
    FilmInputSchema,
    PopulateDBResponse,
    StarshipInputSchema,
)
from api.core.populatedb.service import PopulateDBService
from api.domains.characters.models import Character
from api.domains.films.models import Film
from api.domains.starships.models import Starship


@pytest.fixture
def mock_repositories(mocker):
    """Mock repositories."""
    char_repo = mocker.MagicMock()
    film_repo = mocker.MagicMock()
    starship_repo = mocker.MagicMock()

    char_repo._extract_id_from_url.return_value = 1
    film_repo._extract_id_from_url.return_value = 1
    starship_repo._extract_id_from_url.return_value = 1

    return char_repo, film_repo, starship_repo


@pytest.fixture
def service(mocker, mock_db_session, mock_settings, mock_repositories):
    """Create PopulateDBService instance with mocked dependencies."""
    # Update mock_settings to match the service's expected base URL
    mock_settings.swapi_base_url = "https://api.example.com"

    mocker.patch("api.core.populatedb.service.get_settings", return_value=mock_settings)
    mocker.patch(
        "api.core.populatedb.service.CharacterRepository",
        return_value=mock_repositories[0],
    )
    mocker.patch(
        "api.core.populatedb.service.FilmRepository", return_value=mock_repositories[1]
    )
    mocker.patch(
        "api.core.populatedb.service.StarshipRepository",
        return_value=mock_repositories[2],
    )

    return PopulateDBService(mock_db_session)


@pytest.fixture
def sample_film_data():
    """Sample film data for testing."""
    return {
        "title": "A New Hope",
        "episode_id": 4,
        "opening_crawl": "It is a period of civil war...",
        "director": "George Lucas",
        "producer": "Gary Kurtz, Rick McCallum",
        "release_date": "1977-05-25",
        "characters": ["https://api.example.com/people/1/"],
        "planets": ["https://api.example.com/planets/1/"],
        "starships": ["https://api.example.com/starships/2/"],
        "vehicles": [],
        "species": ["https://api.example.com/species/1/"],
        "created": "2014-12-10T14:23:31.880000Z",
        "edited": "2014-12-20T19:49:45.256000Z",
        "url": "https://api.example.com/films/1/",
    }


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "name": "Luke Skywalker",
        "height": "172",
        "mass": "77",
        "hair_color": "blond",
        "skin_color": "fair",
        "eye_color": "blue",
        "birth_year": "19BBY",
        "gender": "male",
        "homeworld": "https://api.example.com/planets/1/",
        "films": ["https://api.example.com/films/1/"],
        "species": [],
        "vehicles": ["https://api.example.com/vehicles/14/"],
        "starships": ["https://api.example.com/starships/12/"],
        "created": "2014-12-09T13:50:51.644000Z",
        "edited": "2014-12-20T21:17:56.891000Z",
        "url": "https://api.example.com/people/1/",
    }


@pytest.fixture
def sample_starship_data():
    """Sample starship data for testing."""
    return {
        "name": "X-wing",
        "model": "T-65 X-wing",
        "manufacturer": "Incom Corporation",
        "cost_in_credits": "149999",
        "length": "12.5",
        "max_atmosphering_speed": "1050",
        "crew": "1",
        "passengers": "0",
        "cargo_capacity": "110",
        "consumables": "1 week",
        "hyperdrive_rating": "1.0",
        "MGLT": "100",
        "starship_class": "Starfighter",
        "pilots": ["https://api.example.com/people/1/"],
        "films": ["https://api.example.com/films/1/"],
        "created": "2014-12-12T11:19:05.340000Z",
        "edited": "2014-12-20T21:23:49.886000Z",
        "url": "https://api.example.com/starships/12/",
    }


class TestPopulateDBService:
    """Test cases for PopulateDBService."""

    @pytest.mark.asyncio
    async def test_parse_swapi_data_success(self, mocker, service, sample_film_data):
        """Test successful parsing of SWAPI data."""
        mock_response_data = [sample_film_data]

        mock_response = mocker.AsyncMock()
        mock_response.status = 200
        mock_response.read = mocker.AsyncMock(
            return_value=orjson.dumps(mock_response_data)
        )

        mock_aiohttp_session(mocker, mock_response)

        result = await service._parse_swapi_data("films", FilmInputSchema)

        assert len(result) == 1
        assert isinstance(result[0], FilmInputSchema)
        assert result[0].title == "A New Hope"

    @pytest.mark.asyncio
    async def test_parse_swapi_data_http_error(self, mocker, service):
        """Test handling of HTTP errors during SWAPI data parsing."""
        mock_response = mocker.MagicMock()
        mock_response.status = 404
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=mocker.MagicMock(), history=mocker.MagicMock(), status=404
        )

        mock_aiohttp_session(mocker, mock_response)

        with pytest.raises(ExternalServiceException):
            await service._parse_swapi_data("films", FilmInputSchema)

    @pytest.mark.asyncio
    async def test_parse_swapi_data_json_decode_error(self, mocker, service):
        """Test handling of JSON decode errors."""
        mock_response = mocker.AsyncMock()
        mock_response.status = 200
        mock_response.read = mocker.AsyncMock(return_value=b"invalid json")

        mock_aiohttp_session(mocker, mock_response)

        with pytest.raises(ExternalServiceException) as exc_info:
            await service._parse_swapi_data("films", FilmInputSchema)

        assert "Invalid JSON response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_swapi_data_validation_error(self, mocker, service):
        """Test handling of validation errors."""
        invalid_data = [{"invalid": "data"}]

        mock_response = mocker.AsyncMock()
        mock_response.status = 200
        mock_response.read = mocker.AsyncMock(return_value=orjson.dumps(invalid_data))

        mock_aiohttp_session(mocker, mock_response)

        with pytest.raises(InputValidationException):
            await service._parse_swapi_data("films", FilmInputSchema)

    def test_map_film_input_to_model(self, mocker, service, sample_film_data):
        """Test mapping FilmInputSchema to Film model."""
        film_input = FilmInputSchema(**sample_film_data)

        mock_map = mocker.patch.object(service, "_map_input_to_model")
        service._map_film_input_to_model(film_input)

        mock_map.assert_called_once()
        args, kwargs = mock_map.call_args
        assert args[0] == film_input
        assert args[1] == Film
        assert "field_transformers" in kwargs
        assert "release_date" in kwargs["field_transformers"]

    def test_map_character_input_to_model(self, mocker, service, sample_character_data):
        """Test mapping CharacterInputSchema to Character model."""
        character_input = CharacterInputSchema(**sample_character_data)

        mock_map = mocker.patch.object(service, "_map_input_to_model")
        service._map_character_input_to_model(character_input)

        mock_map.assert_called_once()
        args, kwargs = mock_map.call_args
        assert args[0] == character_input
        assert args[1] == Character
        assert "nullable_fields" in kwargs
        assert "height" in kwargs["nullable_fields"]

    def test_map_starship_input_to_model(self, mocker, service, sample_starship_data):
        """Test mapping StarshipInputSchema to Starship model."""
        starship_input = StarshipInputSchema(**sample_starship_data)

        mock_map = mocker.patch.object(service, "_map_input_to_model")
        service._map_starship_input_to_model(starship_input)

        mock_map.assert_called_once()
        args, kwargs = mock_map.call_args
        assert args[0] == starship_input
        assert args[1] == Starship
        assert "field_mappings" in kwargs
        assert kwargs["field_mappings"]["MGLT"] == "mglt"

    def test_map_input_to_model_basic(self, mocker, service):
        """Test basic functionality of _map_input_to_model."""
        mock_model_class = mocker.MagicMock()
        mock_table = mocker.MagicMock()

        # Create mock columns with proper name attributes
        mock_title_col = mocker.MagicMock()
        mock_title_col.name = "title"
        mock_episode_col = mocker.MagicMock()
        mock_episode_col.name = "episode_id"

        mock_table.columns = [mock_title_col, mock_episode_col]
        mock_model_class.__table__ = mock_table

        input_data = mocker.MagicMock()
        input_data.model_dump.return_value = {
            "title": "Test",
            "episode_id": 1,
            "extra_field": "ignored",
        }

        service._map_input_to_model(input_data, mock_model_class)

        mock_model_class.assert_called_once_with(title="Test", episode_id=1)

    def test_map_input_to_model_with_field_mappings(self, mocker, service):
        """Test _map_input_to_model with field mappings."""
        mock_model_class = mocker.MagicMock()
        mock_table = mocker.MagicMock()

        mock_mglt_col = mocker.MagicMock()
        mock_mglt_col.name = "mglt"
        mock_table.columns = [mock_mglt_col]
        mock_model_class.__table__ = mock_table

        input_data = mocker.MagicMock()
        input_data.model_dump.return_value = {"MGLT": "100"}

        field_mappings = {"MGLT": "mglt"}

        service._map_input_to_model(
            input_data, mock_model_class, field_mappings=field_mappings
        )

        mock_model_class.assert_called_once_with(mglt="100")

    def test_map_input_to_model_with_nullable_fields(self, mocker, service):
        """Test _map_input_to_model with nullable fields."""
        mock_model_class = mocker.MagicMock()
        mock_table = mocker.MagicMock()

        mock_height_col = mocker.MagicMock()
        mock_height_col.name = "height"
        mock_table.columns = [mock_height_col]
        mock_model_class.__table__ = mock_table

        input_data = mocker.MagicMock()
        input_data.model_dump.return_value = {"height": "unknown"}

        nullable_fields = {"height"}

        service._map_input_to_model(
            input_data, mock_model_class, nullable_fields=nullable_fields
        )

        mock_model_class.assert_called_once_with(height=None)

    def test_map_input_to_model_with_transformers(self, mocker, service):
        """Test _map_input_to_model with field transformers."""
        mock_model_class = mocker.MagicMock()
        mock_table = mocker.MagicMock()

        mock_value_col = mocker.MagicMock()
        mock_value_col.name = "value"
        mock_table.columns = [mock_value_col]
        mock_model_class.__table__ = mock_table

        input_data = mocker.MagicMock()
        input_data.model_dump.return_value = {"value": "test"}

        field_transformers = {"value": lambda x: x.upper()}

        service._map_input_to_model(
            input_data, mock_model_class, field_transformers=field_transformers
        )

        mock_model_class.assert_called_once_with(value="TEST")

    @pytest.mark.asyncio
    async def test_populate_with_associations_success(
        self,
        mocker,
        service,
        sample_film_data,
        sample_character_data,
        sample_starship_data,
    ):
        """Test successful population with associations."""
        films_data = [FilmInputSchema(**sample_film_data)]
        people_data = [CharacterInputSchema(**sample_character_data)]
        starships_data = [StarshipInputSchema(**sample_starship_data)]

        # Mock the mapping methods
        mock_film = mocker.MagicMock(spec=Film)
        mock_film.url = sample_film_data["url"]
        mock_film.characters = []
        mock_film.starships = []

        mock_character = mocker.MagicMock(spec=Character)
        mock_character.url = sample_character_data["url"]
        mock_character.starships = []

        mock_starship = mocker.MagicMock(spec=Starship)
        mock_starship.url = sample_starship_data["url"]

        mocker.patch.object(service, "_map_film_input_to_model", return_value=mock_film)
        mocker.patch.object(
            service, "_map_character_input_to_model", return_value=mock_character
        )
        mocker.patch.object(
            service, "_map_starship_input_to_model", return_value=mock_starship
        )

        await service._populate_with_associations(
            films_data, people_data, starships_data
        )

        # Verify entities were added to session
        assert service.db.add.call_count == 3

        # Verify commit was called
        service.db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_populate_with_associations_database_error(
        self, mocker, service, sample_film_data
    ):
        """Test handling of database errors during population."""
        films_data = [FilmInputSchema(**sample_film_data)]
        people_data = []
        starships_data = []

        mock_film = mocker.MagicMock(spec=Film)
        mock_film.url = sample_film_data["url"]
        mock_film.characters = []
        mock_film.starships = []

        service.db.commit.side_effect = SQLAlchemyError("Database error")

        mocker.patch.object(service, "_map_film_input_to_model", return_value=mock_film)

        with pytest.raises(DatabaseException):
            await service._populate_with_associations(
                films_data, people_data, starships_data
            )

        service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_populatedb_wrapper_success(self, mocker, service):
        """Test successful execution of populatedb_wrapper."""
        mock_films = [mocker.MagicMock()]
        mock_people = [mocker.MagicMock()]
        mock_starships = [mocker.MagicMock()]

        mock_parse = mocker.patch.object(service, "_parse_swapi_data")
        mock_parse.side_effect = [mock_films, mock_people, mock_starships]

        mock_populate = mocker.patch.object(service, "_populate_with_associations")

        result = await service.populatedb_wrapper()

        assert isinstance(result, PopulateDBResponse)
        assert mock_parse.call_count == 3
        mock_populate.assert_called_once_with(mock_films, mock_people, mock_starships)

    @pytest.mark.asyncio
    async def test_populatedb_wrapper_external_service_exception(self, mocker, service):
        """Test handling of external service exceptions."""
        mock_parse = mocker.patch.object(service, "_parse_swapi_data")
        mock_parse.side_effect = ExternalServiceException("API error")

        with pytest.raises(ExternalServiceException):
            await service.populatedb_wrapper()

        service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_populatedb_wrapper_database_exception(self, mocker, service):
        """Test handling of database exceptions."""
        mock_parse = mocker.patch.object(service, "_parse_swapi_data")
        mock_parse.return_value = [mocker.MagicMock()]

        mock_populate = mocker.patch.object(service, "_populate_with_associations")
        mock_populate.side_effect = DatabaseException("DB error")

        with pytest.raises(DatabaseException):
            await service.populatedb_wrapper()

        service.db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_populatedb_wrapper_unexpected_exception(self, mocker, service):
        """Test handling of unexpected exceptions."""
        mock_parse = mocker.patch.object(service, "_parse_swapi_data")
        mock_parse.side_effect = Exception("Unexpected error")

        with pytest.raises(InternalServerException) as exc_info:
            await service.populatedb_wrapper()

        assert "An unexpected error occurred" in str(exc_info.value)
        service.db.rollback.assert_called_once()
