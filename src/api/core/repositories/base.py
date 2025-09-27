from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from api.utils.url_helpers import extract_id_from_url

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _extract_id_from_url(self, url: str) -> int:
        """Extract the numeric ID from the URL field.
        - Handles optional trailing slash
        """
        return extract_id_from_url(url)

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
