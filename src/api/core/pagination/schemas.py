from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(
        default=10, ge=1, le=100, description="Number of items to return"
    )


class PaginationMeta(BaseModel):
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Items per page")
    has_next: bool = Field(description="Whether there are more items")
    has_previous: bool = Field(description="Whether there are previous items")
    next_offset: Optional[int] = Field(default=None, description="Offset for next page")
    previous_offset: Optional[int] = Field(
        default=None, description="Offset for previous page"
    )


class PaginatedResponse(BaseModel, Generic[T]):
    meta: PaginationMeta = Field(description="Pagination metadata")
    items: list[T] = Field(description="List of items")
