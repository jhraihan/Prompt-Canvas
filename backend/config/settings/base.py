from datetime import timedelta
from pathlib import Path

import environ

from config.logging import logging_config
from config.observability import init_error_tracking

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    HF_MODEL=(str, "black-forest-labs/FLUX.1-schnell"),
    HF_PROVIDER=(str, "auto"),
    HF_TIMEOUT=(int, 120),
    IMAGE_PROVIDER=(str, "huggingface"),
    IMAGE_STORAGE=(str, "local"),
    MEDIA_BASE_URL=(str, ""),
    GENERATION_RATE=(str, "20/hour"),
    ANON_RATE=(str, "30/hour"),
    USER_RATE=(str, "300/hour"),
    LOG_JSON=(bool, True),
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, "production"),
    SENTRY_RELEASE=(str, ""),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.0),
    LOGIN_RATE=(str, "10/hour"),
    REGISTER_RATE=(str, "10/hour"),
    TOKEN_RATE=(str, "60/hour"),
    PASSWORD_RESET_RATE=(str, "5/hour"),
    EMAIL_BACKEND=(str, "django.core.mail.backends.smtp.EmailBackend"),
    EMAIL_HOST=(str, ""),
    EMAIL_PORT=(int, 587),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_USE_SSL=(bool, False),
    DEFAULT_FROM_EMAIL=(str, "Prompt Canvas <noreply@localhost>"),
    FRONTEND_BASE_URL=(str, ""),
    PASSWORD_RESET_TIMEOUT=(int, 3600),
    EMAIL_VERIFICATION_TIMEOUT=(int, 86400 * 3),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "accounts",
    "images",
]

MIDDLEWARE = [
    "config.logging.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = 60

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_BASE_URL = env("MEDIA_BASE_URL", default="")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_PAGINATION_CLASS": "images.pagination.HistoryPagination",
    "PAGE_SIZE": 12,
    "EXCEPTION_HANDLER": "config.exception_handler.promptcanvas_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("ANON_RATE"),
        "user": env("USER_RATE"),
        "generation": env("GENERATION_RATE"),
        "login": env("LOGIN_RATE"),
        "register": env("REGISTER_RATE"),
        "token": env("TOKEN_RATE"),
        "password_reset": env("PASSWORD_RESET_RATE"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

AUTH_COOKIE_REFRESH = "pc_refresh"
AUTH_COOKIE_PATH = "/api/auth/"
AUTH_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = "None"
AUTH_COOKIE_DOMAIN = None

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "origin",
    "user-agent",
)

IMAGE_PROVIDER = env("IMAGE_PROVIDER")
IMAGE_STORAGE = env("IMAGE_STORAGE")
HF_TOKEN = env("HF_TOKEN", default="")
HF_MODEL = env("HF_MODEL")
HF_PROVIDER = env("HF_PROVIDER")
HF_TIMEOUT = env("HF_TIMEOUT")

SPECTACULAR_SETTINGS = {
    "TITLE": "Prompt Canvas API",
    "DESCRIPTION": (
        "Generate images from natural language prompts.\n\n"
        "Every image endpoint requires `Authorization: Bearer <access token>`. "
        "The refresh token is an httpOnly cookie the browser supplies on its "
        "own -- it is never in a response body and cannot be read by script."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "SizeEnum": "images.constants.SIZE_CHOICES",
        "QualityEnum": "images.constants.QUALITY_CHOICES",
    },
    "SERVERS": [{"url": "/", "description": "This server"}],
    "TAGS": [
        {"name": "auth", "description": "Accounts, sessions, and recovery."},
        {"name": "images", "description": "Generation and history."},
        {"name": "sharing", "description": "Share links."},
        {"name": "system", "description": "Health and options."},
    ],
}

MAILERS = {
    "default": {
        "BACKEND": env("EMAIL_BACKEND"),
        "OPTIONS": {
            "host": env("EMAIL_HOST"),
            "port": env("EMAIL_PORT"),
            "username": env("EMAIL_HOST_USER"),
            "password": env("EMAIL_HOST_PASSWORD"),
            "use_tls": env("EMAIL_USE_TLS"),
            "use_ssl": env("EMAIL_USE_SSL"),
            "timeout": 15,
        },
    },
}

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="") or (
    CORS_ALLOWED_ORIGINS[0] if CORS_ALLOWED_ORIGINS else "http://localhost:5173"
)

PASSWORD_RESET_TIMEOUT = env("PASSWORD_RESET_TIMEOUT")
EMAIL_VERIFICATION_TIMEOUT = env("EMAIL_VERIFICATION_TIMEOUT")

LOGGING = logging_config(json_output=env("LOG_JSON"))

ERROR_TRACKING_ENABLED = init_error_tracking(
    dsn=env("SENTRY_DSN"),
    environment=env("SENTRY_ENVIRONMENT"),
    release=env("SENTRY_RELEASE") or None,
    traces_sample_rate=env("SENTRY_TRACES_SAMPLE_RATE"),
)
