import asyncio
from typing import List, Type, TypeVar

import aiohttp
import orjson
from fastapi import Depends
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.settings import get_settings
from api.core.exceptions import ExternalServiceException, InputValidationException
from api.core.populatedb.schemas import (
    CharacterInputSchema,
    FilmInputSchema,
    StarshipInputSchema,
)
from api.domains.characters.repository import CharacterRepository
from api.domains.films.repository import FilmRepository
from api.domains.starships.repository import StarshipRepository
from api.storage.postgres import get_db_session

T = TypeVar("T", bound=BaseModel)


class PopulateDBService:
    """Service for populating database with SWAPI data."""

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db
        self.settings = get_settings()

    async def populatedb(self):
        """Populate database with SWAPI data."""
        # Parse data from SWAPI concurrently
        films_data, people_data, starships_data = await asyncio.gather(
            self._parse_swapi_data("films", FilmInputSchema),
            self._parse_swapi_data("people", CharacterInputSchema),
            self._parse_swapi_data("starships", StarshipInputSchema),
        )

        # Populate database sequentially (due to potential relationships)
        await self._populate_films(films_data)
        await self._populate_starships(starships_data)
        await self._populate_characters(people_data)

    async def _populate_films(self, films_data: List[FilmInputSchema]):
        """Populate films data from SWAPI."""
        film_repo = FilmRepository(self.db)
        # TODO: Implement film population logic using films_data

    async def _populate_starships(self, starships_data: List[StarshipInputSchema]):
        """Populate starships data from SWAPI."""
        starship_repo = StarshipRepository(self.db)
        # TODO: Implement starship population logic using starships_data

    async def _populate_characters(self, people_data: List[CharacterInputSchema]):
        """Populate characters data from SWAPI."""
        character_repo = CharacterRepository(self.db)
        # TODO: Implement character population logic using people_data

    async def _parse_swapi_data(self, path: str, schema_class: Type[T]) -> List[T]:
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
