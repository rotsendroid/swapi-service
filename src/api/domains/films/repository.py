from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.base_repository import BaseRepository
from api.core.exceptions import DatabaseException
from api.domains.films.models import Film


class FilmRepository(BaseRepository[Film]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    def get_count_query(self, title: str | None = None):
        """Return base query for counting films."""
        stmt = select(Film)
        if title:
            stmt = stmt.where(Film.title.ilike(f"%{title}%"))
        return stmt

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Film]:
        try:
            stmt = (
                select(Film)
                .options(selectinload(Film.characters), selectinload(Film.starships))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve films: {str(e)}") from e

    async def get_by_title(
        self, title: str, skip: int = 0, limit: int = 100
    ) -> list[Film]:
        try:
            stmt = (
                select(Film)
                .options(selectinload(Film.characters), selectinload(Film.starships))
                .where(Film.title.ilike(f"%{title}%"))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseException(
                f"Failed to retrieve films by title '{title}': {str(e)}"
            ) from e

    async def get_by_url(self, url: str) -> Optional[Film]:
        try:
            stmt = (
                select(Film)
                .options(selectinload(Film.characters), selectinload(Film.starships))
                .where(Film.url == url)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(
                f"Failed to retrieve film by URL '{url}': {str(e)}"
            ) from e

    async def update(self, obj: Film) -> Film:
        try:
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to update film: {str(e)}") from e
