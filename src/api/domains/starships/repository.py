from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.repositories.base import BaseRepository
from api.domains.starships.models import Starship


class StarshipRepository(BaseRepository[Starship]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, id: int) -> Optional[Starship]:
        stmt = (
            select(Starship)
            .options(selectinload(Starship.pilots), selectinload(Starship.films))
            .where(Starship.id == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Starship]:
        stmt = (
            select(Starship)
            .options(selectinload(Starship.pilots), selectinload(Starship.films))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: Starship) -> Starship:
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_by_name(self, name: str) -> Optional[Starship]:
        stmt = (
            select(Starship)
            .options(selectinload(Starship.pilots), selectinload(Starship.films))
            .where(Starship.name == name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
