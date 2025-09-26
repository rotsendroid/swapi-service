from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.exceptions import ConflictException, DatabaseException
from api.core.repositories.base import BaseRepository
from api.domains.films.models import Film


class FilmRepository(BaseRepository[Film]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, id: int) -> Optional[Film]:
        try:
            stmt = (
                select(Film)
                .options(selectinload(Film.characters), selectinload(Film.starships))
                .where(Film.id == id)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve film by ID {id}: {str(e)}") from e

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Film]:
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

    async def create(self, obj: Film) -> Film:
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictException("Film with this data already exists") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to create film: {str(e)}") from e

    async def get_by_title(self, title: str) -> Optional[Film]:
        try:
            stmt = (
                select(Film)
                .options(selectinload(Film.characters), selectinload(Film.starships))
                .where(Film.title == title)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve film by title '{title}': {str(e)}") from e
