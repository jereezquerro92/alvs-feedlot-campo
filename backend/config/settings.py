"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Governed by: [[adr-02-initial-stack]] · [[adr-06-cache]] · [[adr-16-async-mandatory]]
Docs: [[BACKEND]] · [[VARIABLES]]
LIVE-DOC:END"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name, default=None):
    return os.environ.get(name, default)


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default=""):
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_allowlist(name):
    # Comma-separated `email:group` pairs; group omitted -> "admins"
    # (docs/VARIABLES.md, adr-21). Emails lowercase for case-insensitive match.
    entries = {}
    for item in _env_list(name):
        email, _, group = item.partition(":")
        if email.strip():
            entries[email.strip().lower()] = group.strip() or "admins"
    return entries


DEBUG = _env_bool("DEBUG", False)

SECRET_KEY = _env("SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "SECRET_KEY is not set and DEBUG is False; refusing to boot with "
            "the insecure fallback (docs/VARIABLES.md)."
        )
    SECRET_KEY = "insecure-local-only-change-me"

ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


def _ecs_task_ip():
    uri = os.environ.get("ECS_CONTAINER_METADATA_URI_V4")
    if not uri:
        return None
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(uri, timeout=1) as response:
            data = json.load(response)
    except Exception:
        return None
    for network in data.get("Networks", []):
        for address in network.get("IPv4Addresses", []):
            if address:
                return address
    return None


_ecs_task_ip_value = _ecs_task_ip()
if _ecs_task_ip_value and _ecs_task_ip_value not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_ecs_task_ip_value)

AUTH_DEV_MODE = _env_bool("AUTH_DEV_MODE", False)

AUTH_BOOTSTRAP_ALLOWLIST = _env_allowlist("AUTH_BOOTSTRAP_ALLOWLIST")

if _env_bool("USE_X_FORWARDED_PROTO", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 3600
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "apps.health",
    "apps.users",
    "apps.m365",
    "apps.router",
    # Feedlot domain (Phase 1) — docs/FEEDLOT.md
    "apps.clients",
    "apps.ledger",
    "apps.livestock",
    "apps.feed",
    "apps.sanitary",
    "apps.metrics",
    "apps.market",
]

MIDDLEWARE = [
    "config.middleware.EnsureCacheControlMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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

ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("DB_NAME", "app"),
        "USER": _env("DB_USER", "app"),
        "PASSWORD": _env("DB_PASSWORD", "app"),
        "HOST": _env("DB_HOST", "localhost"),
        "PORT": _env("DB_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache_table",
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
            "CULL_FREQUENCY": 3,
        },
    },
    "locmem": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
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
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

COGNITO_USER_POOL_ID = _env("COGNITO_USER_POOL_ID", "")
COGNITO_CLIENT_ID = _env("COGNITO_CLIENT_ID", "")
COGNITO_CLIENT_SECRET = _env("COGNITO_CLIENT_SECRET", "")
COGNITO_DOMAIN = _env("COGNITO_DOMAIN", "")
COGNITO_REGION = _env("COGNITO_REGION", "us-east-1")

# Post-auth destinations ([[VARIABLES]]). Default "/" is right in cloud, where
# the ALB serves frontend and backend from one origin; locally the two run on
# split ports, so compose points these at the frontend origin so login/logout
# land the user back on the app ([[AUTH]], [[INFRASTRUCTURE]]).
LOGIN_REDIRECT_URL = _env("LOGIN_REDIRECT_URL", "/")
LOGOUT_REDIRECT_URL = _env("LOGOUT_REDIRECT_URL", "/")

THROTTLE_COOLDOWN_SECONDS = int(_env("THROTTLE_COOLDOWN_SECONDS", "2"))

# Router silent rate-abuse guard (#371, [[VARIABLES]], [[adr-16-async-mandatory]],
# [[adr-06-cache]] — state lives in the shared DatabaseCache, no Redis).
ROUTER_RATE_IDLE_SKIP_SECONDS = int(_env("ROUTER_RATE_IDLE_SKIP_SECONDS", "20"))
ROUTER_RATE_THRESHOLD_PER_MINUTE = float(_env("ROUTER_RATE_THRESHOLD_PER_MINUTE", "20"))
ROUTER_RATE_BLOCK_SECONDS = int(_env("ROUTER_RATE_BLOCK_SECONDS", "300"))

# Router audit retention window in days ([[CHATBOT]] — Retention, #65).
# `purge_router_audit` deletes IntentQuery rows older than this by created_at.
ROUTER_AUDIT_RETENTION_DAYS = int(_env("ROUTER_AUDIT_RETENTION_DAYS", "30"))

# Kill switch for the router choosing tier ([[CHATBOT]], [[adr-15-chatbot-two-tier]]):
# false short-circuits POST /api/router/route/ to 503 before any inference call.
ROUTER_ENABLED = _env_bool("ROUTER_ENABLED", True)

# Bedrock inference for the router choosing tier ([[VARIABLES]], [[CHATBOT]]).
# The model ID must be the cross-region inference-profile form
# (us.amazon.nova-micro-v1:0) — the bare ID is not on-demand invokable.
BEDROCK_REGION = _env("BEDROCK_REGION", "us-east-1")
ROUTER_BEDROCK_MODEL_ID = _env("ROUTER_BEDROCK_MODEL_ID", "us.amazon.nova-micro-v1:0")

MSGRAPH_TENANT_ID = _env("MSGRAPH_TENANT_ID", "")
MSGRAPH_CLIENT_ID = _env("MSGRAPH_CLIENT_ID", "")
MSGRAPH_CLIENT_SECRET = _env("MSGRAPH_CLIENT_SECRET", "")

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
if DEBUG and AUTH_DEV_MODE:
    AUTHENTICATION_BACKENDS.append("apps.users.backends.DevLoginBackend")

CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _env_list("CSRF_TRUSTED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

PROJECT_SLUG = _env("PROJECT_SLUG", "astro-drf-aws")

SPECTACULAR_SETTINGS = {
    "TITLE": f"{PROJECT_SLUG} backend",
    "DESCRIPTION": "Django 6 + DRF backend service.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}
