from typing import Any, Callable, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import PaginatedResponse, PaginationMeta, PaginationParams

T = TypeVar("T")


class PaginationService(Generic[T]):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def paginate_with_repository(
        self,
        repository_get_all: Callable[[int, int], Any],
        count_query_stmt: Any,
        params: PaginationParams,
        serializer: Callable[[list[Any]], list[T]],
    ) -> PaginatedResponse[T]:
        # Get total count using the provided count query statement
        count_stmt = select(func.count()).select_from(count_query_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Use repository's get_all method with offset (skip) and limit
        items = await repository_get_all(skip=params.offset, limit=params.limit)  # type: ignore

        # Serialize items
        serialized_items = serializer(items)

        # Calculate pagination metadata
        has_next = (params.offset + params.limit) < total
        has_previous = params.offset > 0

        next_offset = params.offset + params.limit if has_next else None
        previous_offset = max(0, params.offset - params.limit) if has_previous else None

        meta = PaginationMeta(
            total=total,
            offset=params.offset,
            limit=params.limit,
            has_next=has_next,
            has_previous=has_previous,
            next_offset=next_offset,
            previous_offset=previous_offset,
        )

        return PaginatedResponse(items=serialized_items, meta=meta)
