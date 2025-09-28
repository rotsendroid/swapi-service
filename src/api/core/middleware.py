from typing import Callable

from fastapi import Request, Response
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.config.logging import get_logger
from api.core.exceptions import BaseServiceException

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    def __init__(
        self, app, log_request_body: bool = False, log_response_body: bool = False
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger.info("Incoming request")

        # Process request
        try:
            response = await call_next(request)
        except Exception:
            # Log unhandled exceptions
            logger.error(
                "Request failed with unhandled exception",
                exc_info=True,
            )
            raise

        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        else:
            log_level = "info"

        # Log response
        getattr(logger, log_level)("Request completed")

        return response


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Centralized exception handler middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except BaseServiceException as e:
            logger.warning(
                f"{e.__class__.__name__}: {e.message}",
                extra={"error_code": e.error_code, "details": e.details},
            )
            error_response = e.to_response_schema()
            return ORJSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump(),
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            return ORJSONResponse(
                status_code=500,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                },
            )
