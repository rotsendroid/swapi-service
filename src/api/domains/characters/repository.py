from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.exceptions import ConflictException, DatabaseException
from api.core.repositories.base import BaseRepository
from api.domains.characters.models import Character


class CharacterRepository(BaseRepository[Character]):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, id: int) -> Optional[Character]:
        try:
            stmt = (
                select(Character)
                .options(selectinload(Character.films), selectinload(Character.starships))
                .where(Character.id == id)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve character by ID {id}: {str(e)}") from e

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Character]:
        try:
            stmt = (
                select(Character)
                .options(selectinload(Character.films), selectinload(Character.starships))
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve characters: {str(e)}") from e

    async def create(self, obj: Character) -> Character:
        try:
            self.session.add(obj)
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except IntegrityError as e:
            await self.session.rollback()
            raise ConflictException(f"Character with this data already exists") from e
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise DatabaseException(f"Failed to create character: {str(e)}") from e

    async def get_by_name(self, name: str) -> Optional[Character]:
        try:
            stmt = (
                select(Character)
                .options(selectinload(Character.films), selectinload(Character.starships))
                .where(Character.name == name)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve character by name '{name}': {str(e)}") from e
