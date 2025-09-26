from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.repositories.base import BaseRepository
from api.domains.films.models import Film


class FilmRepository(BaseRepository[Film]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, id: int) -> Optional[Film]:
        stmt = (
            select(Film)
            .options(selectinload(Film.characters), selectinload(Film.starships))
            .where(Film.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Film]:
        stmt = (
            select(Film)
            .options(selectinload(Film.characters), selectinload(Film.starships))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: Film) -> Film:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_by_title(self, title: str) -> Optional[Film]:
        stmt = (
            select(Film)
            .options(selectinload(Film.characters), selectinload(Film.starships))
            .where(Film.title == title)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
