"""Tests for core middleware functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from fastapi import Request, Response
from fastapi.responses import ORJSONResponse

from api.core.middleware import RequestLoggingMiddleware, ExceptionHandlerMiddleware
from api.core.exceptions import BaseServiceException


class TestRequestLoggingMiddleware:
    """Test cases for RequestLoggingMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application."""
        return MagicMock()

    @pytest.fixture
    def mock_request(self):
        """Mock HTTP request."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = "http://test.com/api/test"
        return request

    @pytest.fixture
    def mock_logger(self, mocker):
        """Mock logger for testing."""
        return mocker.patch("api.core.middleware.logger")

    def test_middleware_initialization_default(self, mock_app):
        """Test middleware initialization with default parameters."""
        middleware = RequestLoggingMiddleware(mock_app)

        assert middleware.app == mock_app
        assert middleware.log_request_body is False
        assert middleware.log_response_body is False

    def test_middleware_initialization_custom(self, mock_app):
        """Test middleware initialization with custom parameters."""
        middleware = RequestLoggingMiddleware(
            mock_app, log_request_body=True, log_response_body=True
        )

        assert middleware.app == mock_app
        assert middleware.log_request_body is True
        assert middleware.log_response_body is True

    @pytest.mark.asyncio
    async def test_successful_request_info_level(
        self, mock_app, mock_request, mock_logger
    ):
        """Test logging for successful request (2xx status code)."""
        middleware = RequestLoggingMiddleware(mock_app)

        # Mock successful response
        mock_response = Response(status_code=200)
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)
        mock_logger.info.assert_any_call("Incoming request")
        mock_logger.info.assert_any_call("Request completed")

    @pytest.mark.asyncio
    async def test_client_error_warning_level(
        self, mock_app, mock_request, mock_logger
    ):
        """Test logging for client error (4xx status code)."""
        middleware = RequestLoggingMiddleware(mock_app)

        # Mock client error response
        mock_response = Response(status_code=404)
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)
        mock_logger.info.assert_called_with("Incoming request")
        mock_logger.warning.assert_called_with("Request completed")

    @pytest.mark.asyncio
    async def test_server_error_error_level(self, mock_app, mock_request, mock_logger):
        """Test logging for server error (5xx status code)."""
        middleware = RequestLoggingMiddleware(mock_app)

        # Mock server error response
        mock_response = Response(status_code=500)
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)
        mock_logger.info.assert_called_with("Incoming request")
        mock_logger.error.assert_called_with("Request completed")

    @pytest.mark.asyncio
    async def test_unhandled_exception_logging(
        self, mock_app, mock_request, mock_logger
    ):
        """Test logging for unhandled exceptions."""
        middleware = RequestLoggingMiddleware(mock_app)

        # Mock call_next to raise an exception
        test_exception = Exception("Test error")
        mock_call_next = AsyncMock(side_effect=test_exception)

        with pytest.raises(Exception) as exc_info:
            await middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value == test_exception
        mock_call_next.assert_called_once_with(mock_request)
        mock_logger.info.assert_called_with("Incoming request")
        mock_logger.error.assert_called_with(
            "Request failed with unhandled exception",
            exc_info=True,
        )


class TestExceptionHandlerMiddleware:
    """Test cases for ExceptionHandlerMiddleware."""

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI application."""
        return MagicMock()

    @pytest.fixture
    def mock_request(self):
        """Mock HTTP request."""
        request = MagicMock(spec=Request)
        request.method = "GET"
        request.url = "http://test.com/api/test"
        return request

    @pytest.fixture
    def mock_logger(self, mocker):
        """Mock logger for testing."""
        return mocker.patch("api.core.middleware.logger")

    @pytest.mark.asyncio
    async def test_successful_request_passthrough(self, mock_app, mock_request):
        """Test that successful requests pass through unchanged."""
        middleware = ExceptionHandlerMiddleware(mock_app)

        mock_response = Response(status_code=200, content="success")
        mock_call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert result == mock_response
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_base_service_exception_handling(
        self, mock_app, mock_request, mock_logger
    ):
        """Test handling of BaseServiceException."""
        middleware = ExceptionHandlerMiddleware(mock_app)

        # Create a test BaseServiceException
        test_exception = BaseServiceException(
            message="Test error message",
            error_code="TEST_ERROR",
            status_code=400,
            details={"field": "value"},
        )

        mock_call_next = AsyncMock(side_effect=test_exception)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, ORJSONResponse)
        assert result.status_code == 400

        # Verify logging
        mock_logger.warning.assert_called_once_with(
            f"{test_exception.__class__.__name__}: {test_exception.message}",
            extra={
                "error_code": test_exception.error_code,
                "details": test_exception.details,
            },
        )

    @pytest.mark.asyncio
    async def test_base_service_exception_response_content(
        self, mock_app, mock_request
    ):
        """Test response content for BaseServiceException."""
        middleware = ExceptionHandlerMiddleware(mock_app)

        test_exception = BaseServiceException(
            message="Test error message",
            error_code="TEST_ERROR",
            status_code=422,
            details={"validation": "failed"},
        )

        mock_call_next = AsyncMock(side_effect=test_exception)

        # Verify the response is properly created
        result = await middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, ORJSONResponse)
        assert result.status_code == 422

    @pytest.mark.asyncio
    async def test_generic_exception_handling(
        self, mock_app, mock_request, mock_logger
    ):
        """Test handling of generic exceptions."""
        middleware = ExceptionHandlerMiddleware(mock_app)

        test_exception = ValueError("Generic error")
        mock_call_next = AsyncMock(side_effect=test_exception)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, ORJSONResponse)
        assert result.status_code == 500

        # Verify logging
        mock_logger.error.assert_called_once_with(
            f"Unhandled exception: {str(test_exception)}", exc_info=True
        )

    @pytest.mark.asyncio
    async def test_generic_exception_response_format(self, mock_app, mock_request):
        """Test response format for generic exceptions."""
        middleware = ExceptionHandlerMiddleware(mock_app)

        test_exception = RuntimeError("Runtime error occurred")
        mock_call_next = AsyncMock(side_effect=test_exception)

        result = await middleware.dispatch(mock_request, mock_call_next)

        assert isinstance(result, ORJSONResponse)
        assert result.status_code == 500

    @pytest.mark.asyncio
    async def test_multiple_exception_types(self, mock_app, mock_request, mock_logger):
        """Test that different exception types are handled correctly."""
        middleware = ExceptionHandlerMiddleware(mock_app)

        # Test KeyError
        key_error = KeyError("missing key")
        mock_call_next = AsyncMock(side_effect=key_error)

        result = await middleware.dispatch(mock_request, mock_call_next)
        assert isinstance(result, ORJSONResponse)
        assert result.status_code == 500

        # Reset mock for next test
        mock_logger.reset_mock()

        # Test TypeError
        type_error = TypeError("wrong type")
        mock_call_next = AsyncMock(side_effect=type_error)

        result = await middleware.dispatch(mock_request, mock_call_next)
        assert isinstance(result, ORJSONResponse)
        assert result.status_code == 500
