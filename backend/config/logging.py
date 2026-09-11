import json
import logging
import time
import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")

HEADER = "X-Request-ID"
MAX_ID_LENGTH = 64


def get_request_id():
    return _request_id.get()


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True


class JSONFormatter(logging.Formatter):
    RESERVED = frozenset(
        {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
            "taskName",
            "request_id",
        }
    )

    def format(self, record):
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in self.RESERVED and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = repr(value)

        return json.dumps(payload, default=str)


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger("promptcanvas.request")

    def __call__(self, request):
        incoming = request.headers.get(HEADER, "")
        if incoming and len(incoming) <= MAX_ID_LENGTH and incoming.isprintable():
            request_id = "".join(c for c in incoming if c.isalnum() or c in "-_.")
        else:
            request_id = ""
        request_id = request_id or uuid.uuid4().hex

        token = _request_id.set(request_id)
        request.request_id = request_id
        started = time.monotonic()

        try:
            response = self.get_response(request)
        finally:
            duration_ms = int((time.monotonic() - started) * 1000)
            _request_id.reset(token)

        response[HEADER] = request_id
        self.logger.info(
            "%s %s %s",
            request.method,
            request.path,
            response.status_code,
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "user_id": getattr(getattr(request, "user", None), "pk", None),
            },
        )
        return response


def logging_config(*, json_output, level="INFO"):
    formatter = "json" if json_output else "verbose"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": RequestIDFilter}},
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} [{request_id}] {name} {message}",
                "style": "{",
            },
            "json": {"()": JSONFormatter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": formatter,
                "filters": ["request_id"],
            },
        },
        "root": {"handlers": ["console"], "level": level},
        "loggers": {
            "django.request": {
                "handlers": ["console"],
                "level": "ERROR",
                "propagate": False,
            },
            "promptcanvas": {
                "handlers": ["console"],
                "level": level,
                "propagate": False,
            },
        },
    }
