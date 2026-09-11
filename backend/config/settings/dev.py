from .base import *
from .base import env, logging_config

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

CORS_ALLOWED_ORIGINS = env(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)

AUTH_COOKIE_SECURE = False
AUTH_COOKIE_SAMESITE = "Lax"

MEDIA_BASE_URL = env("MEDIA_BASE_URL", default="") or "http://localhost:8000"

MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}
DEFAULT_FROM_EMAIL = "Prompt Canvas <dev@localhost>"

LOGGING = logging_config(json_output=False, level="INFO")
