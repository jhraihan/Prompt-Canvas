import logging

logger = logging.getLogger("promptcanvas")

SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-csrftoken",
        "password",
        "new_password",
        "current_password",
        "token",
        "access",
        "refresh",
        "hf_token",
        "secret",
        "api_key",
    }
)

REDACTED = "[redacted]"


def _scrub(value):
    if isinstance(value, dict):
        return {
            key: REDACTED if str(key).lower() in SENSITIVE_KEYS else _scrub(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def before_send(event, hint):
    request = event.get("request")
    if isinstance(request, dict):
        for field in ("headers", "cookies", "data", "query_string"):
            if field in request:
                request[field] = (
                    REDACTED if field == "cookies" else _scrub(request[field])
                )

    for entry in event.get("breadcrumbs", {}).get("values", []) or []:
        if isinstance(entry, dict) and "data" in entry:
            entry["data"] = _scrub(entry["data"])

    if isinstance(event.get("extra"), dict):
        event["extra"] = _scrub(event["extra"])

    return event


def init_error_tracking(*, dsn, environment, release=None, traces_sample_rate=0.0):
    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed.")
        return False

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            DjangoIntegration(),
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        send_default_pii=False,
        traces_sample_rate=traces_sample_rate,
        before_send=before_send,
    )
    logger.info("Error tracking enabled for environment=%s", environment)
    return True
