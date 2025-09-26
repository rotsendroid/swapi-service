from typing import Any, Dict, Optional

from pydantic import ValidationError


class BaseServiceException(Exception):
    """Base exception class for all service-related exceptions."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__



class NotFoundException(BaseServiceException):
    """Exception for resource not found errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=404, details=details, error_code="NOT_FOUND"
        )


class ConflictException(BaseServiceException):
    """Exception for resource conflict errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=409, details=details, error_code="CONFLICT"
        )


class ExternalServiceException(BaseServiceException):
    """Exception for external service errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            status_code=502,
            details=details,
            error_code="EXTERNAL_SERVICE_ERROR",
        )


class DatabaseException(BaseServiceException):
    """Exception for database-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=500, details=details, error_code="DATABASE_ERROR"
        )


class RequestValidationException(BaseServiceException):
    """Exception for Pydantic validation errors (overrides FastAPI's 422 response)."""

    def __init__(self, validation_error: ValidationError):
        errors = []
        for error in validation_error.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            errors.append(
                {
                    "field": field_path,
                    "message": error["msg"],
                    "type": error["type"],
                    "input": error.get("input"),
                }
            )

        message = f"Validation failed for {len(errors)} field(s)"
        details = {"validation_errors": errors}
        super().__init__(
            message, status_code=422, details=details, error_code="VALIDATION_ERROR"
        )
