"""Production settings with the server-only pieces relaxed, for local smoke tests.

`just local-prod-smoke` uses this to run the real production configuration on a laptop:
DEBUG off, the committed build instead of the dev server, the same required
settings and the same startup guards as production.

Never deploy with this module. It turns off the TLS redirect and secure cookies
(no TLS terminator in front), serves static files through WhiteNoise instead of
nginx, keeps media on disk instead of S3, and puts the database under /tmp.
"""

import os

SMOKE_DIR = "/tmp/wagtail-local-prod-smoke"

# setdefault, so a real environment always wins over these placeholders
os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "local-smoke-" + "x" * 64)
os.environ.setdefault("ALLOWED_HOSTS", "127.0.0.1,localhost")
os.environ.setdefault("CSRF_TRUSTED_ORIGINS", "https://127.0.0.1,https://localhost")
os.environ.setdefault("WAGTAILADMIN_BASE_URL", "https://127.0.0.1")
os.environ.setdefault("WAGTAIL_SITE_NAME", "Haniel Eldrid")
os.environ.setdefault("DATABASE_PATH", f"{SMOKE_DIR}/database.db")

from .prod import *  # noqa: E402,F401,F403
from .prod import MIDDLEWARE, STORAGES  # noqa: E402

# no TLS terminator in front of a laptop
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# nginx serves static files and S3 serves media in production
MIDDLEWARE = [
    *MIDDLEWARE[:1],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]
STORAGES = {
    **STORAGES,
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
}
STATIC_ROOT = f"{SMOKE_DIR}/staticfiles"
MEDIA_ROOT = f"{SMOKE_DIR}/media"
SERVE_MEDIA = True
