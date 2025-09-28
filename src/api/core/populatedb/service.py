import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Type, TypeVar

import aiohttp
import orjson
from fastapi import Depends
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.settings import get_settings
from api.core.base_repository import BaseRepository
from api.core.exceptions import (
    DatabaseException,
    ExternalServiceException,
    InputValidationException,
    InternalServerException,
)
from api.core.populatedb.schemas import (
    CharacterInputSchema,
    FilmInputSchema,
    PopulateDBResponse,
    StarshipInputSchema,
)
from api.domains.characters.models import Character
from api.domains.characters.repository import CharacterRepository
from api.domains.films.models import Film
from api.domains.films.repository import FilmRepository
from api.domains.starships.models import Starship
from api.domains.starships.repository import StarshipRepository
from api.utils.url_helpers import extract_id_from_url
from api.storage.postgres import Base, get_db_session

T = TypeVar("T", bound=BaseModel)
M = TypeVar("M", bound=Base)
R = TypeVar("R", bound=BaseRepository)


class PopulateDBService:
    """Service for populating database with SWAPI data."""

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db
        self.settings = get_settings()
        self.character_repo = CharacterRepository(db)
        self.film_repo = FilmRepository(db)
        self.starship_repo = StarshipRepository(db)

    async def populatedb_wrapper(self):
        """Populate database with SWAPI data."""
        try:
            # Parse data from SWAPI concurrently
            films_data, people_data, starships_data = await asyncio.gather(
                self._parse_swapi_data("films", FilmInputSchema),
                self._parse_swapi_data("people", CharacterInputSchema),
                self._parse_swapi_data("starships", StarshipInputSchema),
            )

            # create entities with associations
            await self._populate_with_associations(
                films_data, people_data, starships_data
            )

            return PopulateDBResponse()
        except (
            InputValidationException,
            ExternalServiceException,
            DatabaseException,
        ) as e:
            await self.db.rollback()
            raise e
        except Exception as e:
            await self.db.rollback()
            raise InternalServerException(
                "An unexpected error occurred during database population",
                details={"error": str(e)},
            )

    async def _populate_with_associations(
        self,
        films_data: list[FilmInputSchema],
        people_data: list[CharacterInputSchema],
        starships_data: list[StarshipInputSchema],
    ):
        """Create entities with associations using bulk operations.

        Note: We don't use repository create() methods here because:
        1. We need to create all entities first, then establish associations
        2. Repository create() methods commit immediately, which isn't efficient for bulk operations
        3. We handle the ID extraction manually and commit everything at once for better performance
        """
        films = {}
        characters = {}
        starships = {}

        # Create films - extract ID and add to session without commit
        for film_data in films_data:
            film_model = self._map_film_input_to_model(film_data)
            film_model.id = extract_id_from_url(film_model.url)
            films[film_data.url] = film_model

        # Create characters - extract ID and add to session without commit
        for char_data in people_data:
            char_model = self._map_character_input_to_model(char_data)
            char_model.id = extract_id_from_url(char_model.url)
            characters[char_data.url] = char_model

        # Create starships - extract ID and add to session without commit
        for ship_data in starships_data:
            ship_model = self._map_starship_input_to_model(ship_data)
            ship_model.id = extract_id_from_url(ship_model.url)
            starships[ship_data.url] = ship_model

        # Add all entities to session
        for film in films.values():
            self.db.add(film)
        for character in characters.values():
            self.db.add(character)
        for starship in starships.values():
            self.db.add(starship)

        # Establish associations
        for film_data in films_data:
            film = films[film_data.url]

            # Associate characters with film
            for char_url in film_data.characters:
                character = characters.get(char_url)
                if character:
                    film.characters.append(character)

            # Associate starships with film
            for ship_url in film_data.starships:
                starship = starships.get(ship_url)
                if starship:
                    film.starships.append(starship)

        # Character-starship associations
        for char_data in people_data:
            character = characters[char_data.url]

            # Associate starships with character
            for ship_url in char_data.starships:
                starship = starships.get(ship_url)
                if starship and starship not in character.starships:
                    character.starships.append(starship)

        # Commit everything at once
        try:
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(f"Failed to commit database transaction: {str(e)}")

    def _map_input_to_model(
        self,
        input_data: BaseModel,
        model_class: Type[M],
        field_mappings: Optional[Dict[str, str]] = None,
        field_transformers: Optional[Dict[str, Callable[[Any], Any]]] = None,
        nullable_fields: Optional[set[str]] = None,
    ) -> M:
        """Generic method to map input schema to model."""
        field_mappings = field_mappings or {}
        field_transformers = field_transformers or {}
        nullable_fields = nullable_fields or set()

        # Get all fields from input data
        input_dict = input_data.model_dump()
        model_data = {}

        # Get model field names
        model_fields = {field.name for field in model_class.__table__.columns}

        for field_name, value in input_dict.items():
            # Map field name if needed
            target_field = field_mappings.get(field_name, field_name)

            # Skip if target field (input schema field) doesn't exist in model fields
            if target_field not in model_fields:
                continue

            # Handle nullable fields with "unknown" values
            if field_name in nullable_fields and value == "unknown":
                value = None

            # Apply field transformer if available
            if field_name in field_transformers:
                value = field_transformers[field_name](value)

            model_data[target_field] = value

        return model_class(**model_data)

    def _map_film_input_to_model(self, film_input: FilmInputSchema) -> Film:
        """Map FilmInputSchema to Film model."""
        return self._map_input_to_model(
            film_input,
            Film,
            field_transformers={
                "release_date": lambda date_str: datetime.strptime(
                    date_str, "%Y-%m-%d"
                ).date(),
                "created": lambda dt: dt.replace(tzinfo=None) if dt.tzinfo else dt,
                "edited": lambda dt: dt.replace(tzinfo=None) if dt.tzinfo else dt,
            },
        )

    def _map_starship_input_to_model(
        self, starship_input: StarshipInputSchema
    ) -> Starship:
        """Map StarshipInputSchema to Starship model."""
        return self._map_input_to_model(
            starship_input,
            Starship,
            field_mappings={"MGLT": "mglt"},
            field_transformers={
                "created": lambda dt: dt.replace(tzinfo=None) if dt.tzinfo else dt,
                "edited": lambda dt: dt.replace(tzinfo=None) if dt.tzinfo else dt,
            },
        )

    def _map_character_input_to_model(
        self, character_input: CharacterInputSchema
    ) -> Character:
        """Map CharacterInputSchema to Character model."""
        return self._map_input_to_model(
            character_input,
            Character,
            nullable_fields={
                "height",
                "mass",
                "hair_color",
                "skin_color",
                "eye_color",
                "birth_year",
                "gender",
            },
            field_transformers={
                "created": lambda dt: dt.replace(tzinfo=None) if dt.tzinfo else dt,
                "edited": lambda dt: dt.replace(tzinfo=None) if dt.tzinfo else dt,
            },
        )

    async def _parse_swapi_data(self, path: str, schema_class: Type[T]) -> list[T]:
        """Generic method to parse data from SWAPI endpoints."""
        url = f"{self.settings.swapi_base_url}/{path}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        raw_data = orjson.loads(data)
                        return [schema_class(**item) for item in raw_data]
                    else:
                        response.raise_for_status()
                        return []
        except aiohttp.ClientError as e:
            raise ExternalServiceException(
                f"Failed to fetch {path} from SWAPI: {str(e)}"
            )
        except orjson.JSONDecodeError as e:
            raise ExternalServiceException(
                f"Invalid JSON response from SWAPI {path}: {str(e)}"
            )
        except ValidationError as e:
            raise InputValidationException(e)
        except Exception as e:
            raise ExternalServiceException(f"Unexpected error parsing {path}: {str(e)}")
