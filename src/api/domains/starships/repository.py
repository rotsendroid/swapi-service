from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.base_repository import BaseRepository
from api.core.exceptions import DatabaseException
from api.domains.starships.models import Starship


class StarshipRepository(BaseRepository[Starship]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Starship]:
        try:
            stmt = (
                select(Starship)
                .options(selectinload(Starship.pilots), selectinload(Starship.films))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve starships: {str(e)}") from e

    async def get_by_name(self, name: str) -> Optional[Starship]:
        try:
            stmt = (
                select(Starship)
                .options(selectinload(Starship.pilots), selectinload(Starship.films))
                .where(Starship.name == name)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(
                f"Failed to retrieve starship by name '{name}': {str(e)}"
            ) from e

    async def get_by_url(self, url: str) -> Optional[Starship]:
        try:
            stmt = (
                select(Starship)
                .options(selectinload(Starship.pilots), selectinload(Starship.films))
                .where(Starship.url == url)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(
                f"Failed to retrieve starship by URL '{url}': {str(e)}"
            ) from e

    async def update(self, obj: Starship) -> Starship:
        try:
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to update starship: {str(e)}") from e
