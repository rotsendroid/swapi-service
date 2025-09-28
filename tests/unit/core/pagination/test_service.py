"""Tests for PaginationService."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.pagination.schemas import (
    PaginatedResponse,
    PaginationParams,
)
from api.core.pagination.service import PaginationService


@pytest.fixture
def mock_session():
    """Mock async database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def pagination_service(mock_session):
    """PaginationService instance with mocked session."""
    return PaginationService(mock_session)


@pytest.fixture
def sample_pagination_params():
    """Sample pagination parameters for testing."""
    return PaginationParams(offset=0, limit=10)


@pytest.fixture
def sample_pagination_params_with_offset():
    """Sample pagination parameters with offset for testing."""
    return PaginationParams(offset=20, limit=10)


@pytest.fixture
def mock_repository_get_all():
    """Mock repository get_all method."""
    mock = AsyncMock()
    mock.return_value = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"},
    ]
    return mock


@pytest.fixture
def mock_count_query_stmt(mocker):
    """Mock count query statement."""
    mock_stmt = MagicMock()
    # Create a proper mock for the subquery that SQLAlchemy can work with
    mock_subquery = mocker.MagicMock()
    mock_subquery.__class__.__name__ = "Subquery"
    mock_stmt.subquery.return_value = mock_subquery
    return mock_stmt


@pytest.fixture
def sample_serializer():
    """Sample serializer function for testing."""

    def serializer(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"serialized_" + k: v for k, v in item.items()} for item in items]

    return serializer


class TestPaginationService:
    """Test cases for PaginationService."""

    def test_pagination_service_initialization(self, mock_session):
        """Test PaginationService initialization."""
        service = PaginationService(mock_session)
        assert service.session == mock_session

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_first_page(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_pagination_params,
        sample_serializer,
    ):
        """Test pagination for first page with items."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50
        pagination_service.session.execute.return_value = mock_count_result

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=sample_pagination_params,
            serializer=sample_serializer,
        )

        # Verify repository was called with correct parameters
        mock_repository_get_all.assert_called_once_with(skip=0, limit=10)

        # Verify count query was executed
        pagination_service.session.execute.assert_called_once()

        # Verify result structure
        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 3
        assert all("serialized_" in str(item) for item in result.items)

        # Verify pagination metadata
        assert result.meta.total == 50
        assert result.meta.offset == 0
        assert result.meta.limit == 10
        assert result.meta.has_next is True
        assert result.meta.has_previous is False
        assert result.meta.next_offset == 10
        assert result.meta.previous_offset is None

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_middle_page(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_pagination_params_with_offset,
        sample_serializer,
    ):
        """Test pagination for middle page with items."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 50
        pagination_service.session.execute.return_value = mock_count_result

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=sample_pagination_params_with_offset,
            serializer=sample_serializer,
        )

        # Verify repository was called with correct parameters
        mock_repository_get_all.assert_called_once_with(skip=20, limit=10)

        # Verify pagination metadata for middle page
        assert result.meta.total == 50
        assert result.meta.offset == 20
        assert result.meta.limit == 10
        assert result.meta.has_next is True
        assert result.meta.has_previous is True
        assert result.meta.next_offset == 30
        assert result.meta.previous_offset == 10

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_last_page(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_serializer,
    ):
        """Test pagination for last page with items."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 25
        pagination_service.session.execute.return_value = mock_count_result

        # Create pagination params for last page
        params = PaginationParams(offset=20, limit=10)

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=params,
            serializer=sample_serializer,
        )

        # Verify pagination metadata for last page
        assert result.meta.total == 25
        assert result.meta.offset == 20
        assert result.meta.limit == 10
        assert result.meta.has_next is False
        assert result.meta.has_previous is True
        assert result.meta.next_offset is None
        assert result.meta.previous_offset == 10

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_empty_results(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_count_query_stmt,
        sample_pagination_params,
        sample_serializer,
    ):
        """Test pagination with no items."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock empty repository response
        mock_empty_get_all = AsyncMock(return_value=[])

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        pagination_service.session.execute.return_value = mock_count_result

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_empty_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=sample_pagination_params,
            serializer=sample_serializer,
        )

        # Verify empty result
        assert len(result.items) == 0
        assert result.meta.total == 0
        assert result.meta.has_next is False
        assert result.meta.has_previous is False
        assert result.meta.next_offset is None
        assert result.meta.previous_offset is None

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_none_count(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_pagination_params,
        sample_serializer,
    ):
        """Test pagination when count query returns None."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution returning None
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = None
        pagination_service.session.execute.return_value = mock_count_result

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=sample_pagination_params,
            serializer=sample_serializer,
        )

        # Verify that None count is handled as 0
        assert result.meta.total == 0
        assert result.meta.has_next is False
        assert result.meta.has_previous is False

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_exact_page_boundary(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_serializer,
    ):
        """Test pagination when total items exactly match page boundaries."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 30  # Exactly 3 pages of 10
        pagination_service.session.execute.return_value = mock_count_result

        # Test page 3 (offset 20, limit 10) - should be last page
        params = PaginationParams(offset=20, limit=10)

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=params,
            serializer=sample_serializer,
        )

        # Verify pagination metadata for exact boundary
        assert result.meta.total == 30
        assert result.meta.offset == 20
        assert result.meta.limit == 10
        assert result.meta.has_next is False  # No more items
        assert result.meta.has_previous is True
        assert result.meta.next_offset is None
        assert result.meta.previous_offset == 10

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_count_query_construction(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_pagination_params,
        sample_serializer,
    ):
        """Test that count query is properly constructed."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 42
        pagination_service.session.execute.return_value = mock_count_result

        # Mock subquery method
        mock_subquery = MagicMock()
        mock_count_query_stmt.subquery.return_value = mock_subquery

        await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=sample_pagination_params,
            serializer=sample_serializer,
        )

        # Verify that subquery was called on the count query statement
        mock_count_query_stmt.subquery.assert_called_once()

        # Verify session.execute was called
        pagination_service.session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch("api.core.pagination.service.select")
    @patch("api.core.pagination.service.func")
    async def test_paginate_with_repository_previous_offset_edge_case(
        self,
        mock_func,
        mock_select,
        pagination_service,
        mock_repository_get_all,
        mock_count_query_stmt,
        sample_serializer,
    ):
        """Test previous_offset calculation for edge cases."""
        # Mock SQLAlchemy functions
        mock_count_stmt = MagicMock()
        mock_select.return_value.select_from.return_value = mock_count_stmt

        # Mock the count query execution
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 100
        pagination_service.session.execute.return_value = mock_count_result

        # Test with offset=5, limit=10 - previous should be 0, not -5
        params = PaginationParams(offset=5, limit=10)

        result = await pagination_service.paginate_with_repository(
            repository_get_all=mock_repository_get_all,
            count_query_stmt=mock_count_query_stmt,
            params=params,
            serializer=sample_serializer,
        )

        # Verify previous_offset doesn't go below 0
        assert result.meta.previous_offset == 0
        assert result.meta.has_previous is True
