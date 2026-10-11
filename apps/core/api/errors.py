"""Opt-in DRF exception envelope for B02-B10; frozen P01 responses stay unchanged."""

from rest_framework.exceptions import APIException, ErrorDetail, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _plain(value):
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return str(value) if isinstance(value, ErrorDetail) else value


def error_response(code: str, message: str, *, status: int, fields=None) -> Response:
    error = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = _plain(fields)
    return Response({"error": error}, status=status)


def core_exception_handler(exc, context):
    """Let DRF classify HTTP/permission/validation errors; never leak 500 details."""
    response = exception_handler(exc, context)
    if response is None:
        return None  # keep unhandled errors with Django's 500 handler
    if isinstance(exc, ValidationError):
        return error_response(
            "validation_error", "Invalid request data.",
            status=response.status_code, fields=response.data,
        )
    if isinstance(exc, APIException):
        code = exc.get_codes()
        if not isinstance(code, str):
            code = "api_error"
    else:
        code = "permission_denied" if response.status_code == 403 else "not_found"
    detail = (
        response.data.get("detail", "Request failed.")
        if isinstance(response.data, dict) else "Request failed."
    )
    response.data = {"error": {"code": code, "message": str(detail)}}
    return response
