import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import DatabaseError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from images.exceptions import GenerationError

logger = logging.getLogger("promptcanvas.api")


def promptcanvas_exception_handler(exc, context):
    view = context.get("view").__class__.__name__ if context.get("view") else "unknown"

    if isinstance(exc, GenerationError):
        getattr(logger, exc.log_level, logger.error)(
            "%s in %s: %s", exc.__class__.__name__, view, exc
        )
        return Response(
            {"detail": exc.user_message, "code": _code_for(exc)},
            status=exc.status_code,
        )

    if isinstance(exc, DjangoValidationError):
        return Response(
            {"detail": "; ".join(exc.messages), "code": "invalid"}, status=400
        )

    response = drf_exception_handler(exc, context)

    if response is None and isinstance(exc, DatabaseError):
        logger.exception("Database failure in %s", view)
        return Response(
            {
                "detail": "Something went wrong on our side. Please try again.",
                "code": "server_error",
            },
            status=500,
        )

    if response is not None and "code" not in getattr(response, "data", {}):
        if isinstance(response.data, dict):
            response.data.setdefault("code", _default_code(response.status_code))
    return response


def _code_for(exc):
    name = exc.__class__.__name__
    mapping = {
        "ProviderAuthError": "provider_unconfigured",
        "ProviderRateLimited": "rate_limited",
        "ProviderTimeout": "timeout",
        "ProviderUnavailable": "provider_unavailable",
        "ProviderRejectedPrompt": "prompt_rejected",
        "StorageError": "storage_error",
    }
    return mapping.get(name, "generation_failed")


def _default_code(status_code):
    return {
        400: "invalid",
        401: "unauthenticated",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        429: "rate_limited",
    }.get(status_code, "error")
