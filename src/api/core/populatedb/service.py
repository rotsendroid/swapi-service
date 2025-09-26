import asyncio
from typing import List

import aiohttp
import orjson
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.config.settings import get_settings
from api.core.populatedb.schemas import (
    SWAPICharacterInputSchema,
    SWAPIFilmInputSchema,
    SWAPIStarshipInputSchema,
)
from api.domains.characters.repository import CharacterRepository
from api.domains.films.repository import FilmRepository
from api.domains.starships.repository import StarshipRepository
from api.storage.postgres import get_db_session


class PopulateDBService:
    """Service for populating database with SWAPI data."""

    def __init__(self, db: AsyncSession = Depends(get_db_session)):
        self.db = db
        self.settings = get_settings()

    async def populatedb(self):
        """Populate database with SWAPI data."""
        # Parse data from SWAPI concurrently
        films_data, people_data, starships_data = await asyncio.gather(
            self._parse_films(),
            self._parse_people(),
            self._parse_starships()
        )

        # Populate database sequentially (due to potential relationships)
        await self._populate_films(films_data)
        await self._populate_starships(starships_data)
        await self._populate_characters(people_data)

    async def _populate_films(self, films_data: List[SWAPIFilmInputSchema]):
        """Populate films data from SWAPI."""
        film_repo = FilmRepository(self.db)
        # TODO: Implement film population logic using films_data

    async def _populate_starships(self, starships_data: List[SWAPIStarshipInputSchema]):
        """Populate starships data from SWAPI."""
        starship_repo = StarshipRepository(self.db)
        # TODO: Implement starship population logic using starships_data

    async def _populate_characters(self, people_data: List[SWAPICharacterInputSchema]):
        """Populate characters data from SWAPI."""
        character_repo = CharacterRepository(self.db)
        # TODO: Implement character population logic using people_data

    async def _parse_films(self) -> List[SWAPIFilmInputSchema]:
        """Parse films data from SWAPI."""
        url = f"{self.settings.swapi_base_url}/films"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    raw_films = orjson.loads(data)
                    return [SWAPIFilmInputSchema(**film) for film in raw_films]
                else:
                    response.raise_for_status()
                    return []

    async def _parse_people(self) -> List[SWAPICharacterInputSchema]:
        """Parse people (characters) data from SWAPI."""
        url = f"{self.settings.swapi_base_url}/people"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    raw_people = orjson.loads(data)
                    return [SWAPICharacterInputSchema(**person) for person in raw_people]
                else:
                    response.raise_for_status()
                    return []

    async def _parse_starships(self) -> List[SWAPIStarshipInputSchema]:
        """Parse starships data from SWAPI."""
        url = f"{self.settings.swapi_base_url}/starships"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.read()
                    raw_starships = orjson.loads(data)
                    return [SWAPIStarshipInputSchema(**starship) for starship in raw_starships]
                else:
                    response.raise_for_status()
                    return []