"""
Custom exceptions and standard response models.
Mirrors the pattern established in the Backend codebase.
"""
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: Optional[Dict[str, str]] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[ErrorDetail] = None


def create_success_response(
    message: Optional[str] = None,
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
) -> dict:
    """Helper to generate a successful response dictionary following the standard structure."""
    return APIResponse(
        success=True,
        message=message if message is not None else "Operation successful",
        data=data if data is not None else {},
        meta=meta if meta is not None else {},
    ).model_dump()


class BaseAppException(Exception):
    """Base exception for all custom API exceptions"""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        self.meta = meta

        self.error_dict: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.fields:
            self.error_dict["fields"] = self.fields

        super().__init__(self.message)

    def to_response_dict(self) -> dict:
        return {
            "success": False,
            "data": None,
            "meta": self.meta,
            "error": self.error_dict,
        }


# 400 Bad Request
class BadRequestError(BaseAppException):
    def __init__(
        self,
        message: str = "Bad Request",
        fields: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=400,
            code="BAD_REQUEST",
            message=message,
            fields=fields,
            meta=meta,
        )


class ValidationError(BaseAppException):
    def __init__(
        self,
        message: str = "Validation failed",
        fields: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=400,
            code="VALIDATION_ERROR",
            message=message,
            fields=fields,
            meta=meta,
        )


# 401 Unauthorized
class UnauthorizedError(BaseAppException):
    def __init__(
        self,
        message: str = "Unauthorized",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=401,
            code="UNAUTHORIZED",
            message=message,
            meta=meta,
        )


class InvalidCredentialsError(BaseAppException):
    def __init__(
        self,
        message: str = "Invalid credentials",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message=message,
            meta=meta,
        )


class InvalidTokenError(BaseAppException):
    def __init__(
        self,
        message: str = "Invalid authentication token",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=401,
            code="INVALID_TOKEN",
            message=message,
            meta=meta,
        )


class TokenExpiredError(BaseAppException):
    def __init__(
        self,
        message: str = "Authentication token expired",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=401,
            code="TOKEN_EXPIRED",
            message=message,
            meta=meta,
        )


# 403 Forbidden
class ForbiddenError(BaseAppException):
    def __init__(
        self,
        message: str = "Access forbidden",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=403,
            code="FORBIDDEN",
            message=message,
            meta=meta,
        )


class PermissionDeniedError(BaseAppException):
    def __init__(
        self,
        message: str = "Permission denied",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=403,
            code="PERMISSION_DENIED",
            message=message,
            meta=meta,
        )


# 404 Not Found
class NotFoundError(BaseAppException):
    def __init__(
        self,
        message: str = "Resource not found",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=404,
            code="NOT_FOUND",
            message=message,
            meta=meta,
        )


# 409 Conflict
class ConflictError(BaseAppException):
    def __init__(
        self,
        message: str = "Conflict occurred",
        fields: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=409,
            code="CONFLICT",
            message=message,
            fields=fields,
            meta=meta,
        )


class DuplicateResourceError(BaseAppException):
    def __init__(
        self,
        message: str = "Duplicate resource",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=409,
            code="DUPLICATE_RESOURCE",
            message=message,
            meta=meta,
        )


# 410 Gone
class GoneError(BaseAppException):
    def __init__(
        self,
        message: str = "Resource is no longer available",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=410,
            code="GONE",
            message=message,
            meta=meta,
        )


# 422 Unprocessable Entity
class UnprocessableEntityError(BaseAppException):
    def __init__(
        self,
        message: str = "Unprocessable entity",
        fields: Optional[Dict[str, str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=422,
            code="UNPROCESSABLE_ENTITY",
            message=message,
            fields=fields,
            meta=meta,
        )


# 423 Locked
class AccountLockedError(BaseAppException):
    def __init__(
        self,
        message: str = "Account is locked",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=423,
            code="ACCOUNT_LOCKED",
            message=message,
            meta=meta,
        )


# 429 Too Many Requests
class RateLimitedError(BaseAppException):
    def __init__(
        self,
        message: str = "Too many requests",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=429,
            code="RATE_LIMITED",
            message=message,
            meta=meta,
        )


# 500 Internal Server Error
class InternalServerError(BaseAppException):
    def __init__(
        self,
        message: str = "Internal server error",
        meta: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=500,
            code="INTERNAL_ERROR",
            message=message,
            meta=meta,
        )


# Standard error response documentation for OpenAPI / Swagger
STANDARD_ERROR_RESPONSES = {
    400: {"model": APIResponse[None], "description": "Bad Request"},
    401: {"model": APIResponse[None], "description": "Unauthorized"},
    403: {"model": APIResponse[None], "description": "Forbidden"},
    404: {"model": APIResponse[None], "description": "Not Found"},
    409: {"model": APIResponse[None], "description": "Conflict"},
    422: {"model": APIResponse[None], "description": "Validation Error"},
    500: {"model": APIResponse[None], "description": "Internal Server Error"},
}
