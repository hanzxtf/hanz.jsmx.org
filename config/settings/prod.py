from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F401, F403
from .base import DATABASES, STORAGES, env, environ

# The operator fills in the repo file and `just setup-env` installs it here.
ENV_SOURCE = ".env.prod"
ENV_FILE = "/usr/local/etc/wagtail/env"

environ.Env.read_env(ENV_FILE)

HOW_TO_FIX = f"set it in {ENV_SOURCE}, then run `just setup-env` (installs {ENV_FILE})"


def _fail(name, reason):
    raise ImproperlyConfigured(f"{name} {reason}. To fix: {HOW_TO_FIX}")


def _required(name, minimum_length=None):
    value = env(name, default="")
    if not value:
        _fail(name, "is not set")
    if minimum_length and len(value) < minimum_length:
        _fail(name, f"must be at least {minimum_length} characters long")
    return value


def _host_list(name):
    hosts = [item.strip() for item in _required(name).split(",") if item.strip()]
    if not hosts or "*" in hosts:
        _fail(name, "must list the site's real hostnames, never '*'")
    return hosts


def _https_origins(name):
    origins = [item.strip() for item in _required(name).split(",") if item.strip()]
    insecure = [origin for origin in origins if not origin.startswith("https://")]
    if not origins or insecure:
        _fail(
            name,
            f"must list https origins, got: {', '.join(insecure) or 'none'}",
        )
    return origins


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = _required("SECRET_KEY", minimum_length=50)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DJANGO_DEBUG")
if DEBUG:
    _fail("DJANGO_DEBUG", "must be false in production")

if not env("WAGTAILADMIN_BASE_URL", default="").startswith("https://"):
    _fail("WAGTAILADMIN_BASE_URL", "must be the site's https origin in production")

ALLOWED_HOSTS = _host_list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = _https_origins("CSRF_TRUSTED_ORIGINS")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST")
USE_X_FORWARDED_PORT = env("USE_X_FORWARDED_PORT")

# TLS terminates at nginx, which forwards the original scheme and port
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Django-Vite Settings
# ------------------------------------------------------------------------------
DJANGO_VITE = {
    "default": {
        "dev_mode": False,
    }
}

# Wagtail Cache settings
WAGTAIL_CACHE = True
WAGTAIL_CACHE_BACKEND = "default"
WAGTAIL_CACHE_KEYRING = True
WAGTAIL_CACHE_HEADER = "X-App-Cache"
WAGTAIL_CACHE_IGNORE_COOKIES = True

# Wagtail settings
WAGTAIL_SITE_NAME = env("WAGTAIL_SITE_NAME")
WAGTAILADMIN_BASE_URL = env("WAGTAILADMIN_BASE_URL")

# Cache settings
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "wsk-cache",
        "TIMEOUT": 60 * 60 * 24 * 7,  # 1 week
    }
}

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="minioadmin")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="minioadmin")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="bucket")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_VERIFY = True
AWS_QUERYSTRING_AUTH = True
# When using MinIO, we need to set this to False to avoid SSL issues
AWS_S3_SECURE_URLS = env("AWS_S3_SECURE_URLS", default=True)

# Ensure query string authentication is enabled and set expiration
AWS_QUERYSTRING_EXPIRE = env(
    "AWS_QUERYSTRING_EXPIRE", default=1800
)  # 1/2 hour expiration

# Media files are stored in S3-compatible object storage in production
STORAGES = {
    **STORAGES,
    "default": {
        **STORAGES["default"],
        "OPTIONS": {
            **STORAGES["default"].get("OPTIONS", {}),
            "public_endpoint_url": env(
                "AWS_S3_PUBLIC_ENDPOINT_URL", default="http://localhost:9000"
            ),
        },
    },
}

# Database Path
DATABASES = {
    **DATABASES,
    "default": {**DATABASES["default"], "NAME": env("DATABASE_PATH")},
}
