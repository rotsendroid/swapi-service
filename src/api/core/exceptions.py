from typing import Any, Dict, Optional

from pydantic import ValidationError

from api.core.schemas import BaseErrorResponse


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

    def to_response_schema(self) -> BaseErrorResponse:
        """Convert exception to BaseErrorResponse schema."""
        return BaseErrorResponse(
            message=self.message,
            details=str(self.details) if self.details else "",
            status_code=self.status_code,
            error_code=self.error_code,
        )


class NotFoundException(BaseServiceException):
    """Exception for resource not found errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=404, details=details, error_code="NOT_FOUND"
        )

    @classmethod
    def response_example(cls) -> dict:
        """Example response for OpenAPI documentation."""
        # Create instance to get the actual error_code
        instance = cls("Example error")
        return {
            "model": BaseErrorResponse,
            "description": "Resource not found",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Character with id 999 not found",
                        "details": "",
                        "status_code": instance.status_code,
                        "error_code": instance.error_code,
                    }
                }
            },
        }


class ConflictException(BaseServiceException):
    """Exception for resource conflict errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message, status_code=409, details=details, error_code="CONFLICT"
        )

    @classmethod
    def response_example(cls) -> dict:
        """Example response for OpenAPI documentation."""
        # Create instance to get the actual error_code
        instance = cls("Example error")
        return {
            "model": BaseErrorResponse,
            "description": "Resource conflict",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Character with name 'Luke Skywalker' already exists",
                        "details": "",
                        "status_code": instance.status_code,
                        "error_code": instance.error_code,
                    }
                }
            },
        }


class ExternalServiceException(BaseServiceException):
    """Exception for external service errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message,
            status_code=502,
            details=details,
            error_code="EXTERNAL_SERVICE_ERROR",
        )

    @classmethod
    def response_example(cls) -> dict:
        """Example response for OpenAPI documentation."""
        # Create instance to get the actual error_code
        instance = cls("Example error")
        return {
            "model": BaseErrorResponse,
            "description": "External service error",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Failed to fetch people from SWAPI: Connection timeout",
                        "details": "",
                        "status_code": instance.status_code,
                        "error_code": instance.error_code,
                    }
                }
            },
        }


class InputValidationException(BaseServiceException):
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

    @classmethod
    def response_example(cls) -> dict:
        """Example response for OpenAPI documentation."""

        return {
            "model": BaseErrorResponse,
            "description": "Input validation error",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Validation failed for 2 field(s)",
                        "details": "{'validation_errors': [{'field': 'name', 'message': 'field required', 'type': 'missing'}]}",
                        "status_code": 422,
                        "error_code": "VALIDATION_ERROR",
                    }
                }
            },
        }


class InternalServerException(BaseServiceException):
    """Exception for unexpected internal server errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message,
            status_code=500,
            details=details,
            error_code="INTERNAL_SERVER_ERROR",
        )

    @classmethod
    def response_example(cls) -> dict:
        """Example response for OpenAPI documentation."""
        # Create instances to get the actual error_codes
        internal_instance = cls("Example error")
        return {
            "model": BaseErrorResponse,
            "description": "Unexpected internal server error",
            "content": {
                "application/json": {
                    "example": {
                        "internal_error": {
                            "summary": "Internal Server Error",
                            "value": {
                                "message": "An unexpected error occurred during database population",
                                "details": "{'error': 'Unexpected error details'}",
                                "status_code": internal_instance.status_code,
                                "error_code": internal_instance.error_code,
                            },
                        },
                    }
                }
            },
        }


class DatabaseException(InternalServerException):
    """Exception for database-related errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.error_code = "DATABASE_ERROR"
