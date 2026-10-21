from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception with structured error envelope."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.extra = extra or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "code": self.code,
            "message": self.message,
        }
        data.update(self.extra)
        return {"detail": data}


def not_authenticated(message: str = "Authentication required.") -> AppException:
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="NOT_AUTHENTICATED",
        message=message,
    )


def invalid_credentials(message: str = "Invalid username or password.") -> AppException:
    return AppException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code="INVALID_CREDENTIALS",
        message=message,
    )


def account_disabled(message: str = "This account has been disabled.") -> AppException:
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code="ACCOUNT_DISABLED",
        message=message,
    )


def forbidden(message: str = "You do not have permission to perform this action.") -> AppException:
    return AppException(
        status_code=status.HTTP_403_FORBIDDEN,
        code="FORBIDDEN",
        message=message,
    )


def not_found(message: str = "Resource not found.") -> AppException:
    return AppException(
        status_code=status.HTTP_404_NOT_FOUND,
        code="NOT_FOUND",
        message=message,
    )


def duplicate(message: str = "Record already exists.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="DUPLICATE",
        message=message,
    )


def eligibility_failed(reasons: list, message: str = "Donor is not eligible to donate.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="ELIGIBILITY_FAILED",
        message=message,
        extra={"reasons": reasons},
    )


def insufficient_stock(requested: int, available: int, message: str = "Insufficient compatible blood stock available.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="INSUFFICIENT_STOCK",
        message=message,
        extra={"requested": requested, "available": available},
    )


def invalid_status_transition(message: str = "Invalid status transition.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="INVALID_STATUS_TRANSITION",
        message=message,
    )


def referenced_record(message: str = "Cannot delete record because it is referenced by other records.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="REFERENCED_RECORD",
        message=message,
    )


def donor_has_units(message: str = "Cannot modify blood group because donor already has recorded donations.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="DONOR_HAS_UNITS",
        message=message,
    )


def unit_already_issued(message: str = "Cannot delete a blood unit that has already been issued.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="UNIT_ALREADY_ISSUED",
        message=message,
    )


def self_modification_forbidden(message: str = "Administrators cannot modify or delete their own accounts.") -> AppException:
    return AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="SELF_MODIFICATION_FORBIDDEN",
        message=message,
    )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
