import os
import re

from .base import *  # noqa: F401, F403
from .base import env, MIDDLEWARE, environ, BASE_DIR, STORAGES

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# WhiteNoise for serving static files in development
MIDDLEWARE = [
    *MIDDLEWARE[:1],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]


# http://whitenoise.evans.io/en/stable/django.html#WHITENOISE_IMMUTABLE_FILE_TEST
def immutable_file_test(path, url):
    # Match vite (rollup)-generated hashes, à la, `some_file-CSliV9zW.js`
    return re.match(r"^.+[.-][0-9a-zA-Z_-]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

# Django-Vite Settings
# ------------------------------------------------------------------------------
DJANGO_VITE = {
    "default": {
        "dev_mode": True,
        "dev_server_host": "localhost",
        "dev_server_port": 5173,
    }
}

# Disable wagtail cache in development
WAGTAIL_CACHE = False

# Print form notification emails to the console instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEBUG = True
SECRET_KEY = env("SECRET_KEY")

# Wagtail settings
WAGTAIL_SITE_NAME = "Wagtail Starter Kit"
WAGTAILADMIN_BASE_URL = "http://localhost:8000"

# Media files are stored on the local filesystem in development
STORAGES = {
    **STORAGES,
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# SECURITY WARNING: define the correct hosts in production!
# This should be set to your domain or IP address in production
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(",")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS").split(",")
USE_X_FORWARDED_HOST = env("USE_X_FORWARDED_HOST")
USE_X_FORWARDED_PORT = env("USE_X_FORWARDED_PORT")
