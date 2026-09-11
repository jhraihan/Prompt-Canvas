from .base import *

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost"]

IS_NON_PRODUCTION = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
DEFAULT_FROM_EMAIL = "Prompt Canvas <test@localhost>"
FRONTEND_BASE_URL = "http://localhost:5173"

IMAGE_PROVIDER = "stub"
IMAGE_STORAGE = "local"

AUTH_COOKIE_SECURE = False
AUTH_COOKIE_SAMESITE = "Lax"

REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/hour",
        "user": "1000/hour",
        "generation": "1000/hour",
        "login": "1000/hour",
        "register": "1000/hour",
        "token": "1000/hour",
        "password_reset": "1000/hour",
    },
}

LOGGING = logging_config(json_output=False, level="CRITICAL")
