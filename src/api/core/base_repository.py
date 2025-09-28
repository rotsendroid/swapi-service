from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[T]:
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        pass

    @abstractmethod
    async def update(self, obj: T) -> T:
        pass

    @abstractmethod
    async def get_by_url(self, url: str) -> Optional[T]:
        pass
