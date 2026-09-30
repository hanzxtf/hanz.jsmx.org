"""Production configuration must be durable and self-describing."""

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
LITESTREAM = BASE_DIR / "prod/freebsd/litestream/litestream.yml"
ENV_EXAMPLE = BASE_DIR / ".env.prod.example"

INTERVAL_SECONDS = {"s": 1, "m": 60, "h": 3600}


def interval_seconds(value):
    match = re.fullmatch(r"(\d+)([smh])", str(value))
    assert match, f"unparsable interval: {value!r}"
    return int(match.group(1)) * INTERVAL_SECONDS[match.group(2)]


def test_litestream_replicates_frequently_from_the_configured_path():
    config = yaml.safe_load(LITESTREAM.read_text())
    database = config["dbs"][0]
    replica = database["replicas"][0]

    assert database["path"] == "${DATABASE_PATH}"
    assert replica["path"] == "${LITESTREAM_PATH}"
    assert interval_seconds(replica["sync-interval"]) <= 10


def test_env_example_documents_the_required_settings():
    text = ENV_EXAMPLE.read_text()

    for name in [
        "SECRET_KEY",
        "DJANGO_DEBUG",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "WAGTAILADMIN_BASE_URL",
        "DATABASE_PATH",
        "LITESTREAM_PATH",
        "DEFAULT_FROM_EMAIL",
        "EMAIL_HOST",
        "EMAIL_PORT",
        "EMAIL_USE_SSL",
        "EMAIL_TIMEOUT",
    ]:
        assert re.search(
            rf"^{name}=", text, re.M
        ), f"{name} is required by the settings but missing from .env.prod.example"


def test_a_hosted_mail_relay_is_configured_entirely_from_the_environment():
    """Point the site at a relay (Resend, Cloudflare) without touching code.

    Checked in a subprocess because settings are read once at startup, and it
    must be this shape (implicit TLS on 465) rather than the STARTTLS one, since
    an ignored EMAIL_USE_SSL fails the handshake with a confusing error.
    """
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.base",
        "DEFAULT_FROM_EMAIL": "website@hanz.jsmx.org",
        "EMAIL_HOST": "smtp.resend.com",
        "EMAIL_PORT": "465",
        "EMAIL_HOST_USER": "resend",
        "EMAIL_HOST_PASSWORD": "re_123",
        "EMAIL_USE_SSL": "true",
        "EMAIL_USE_TLS": "false",
        "EMAIL_TIMEOUT": "15",
    }
    script = (
        "import django; django.setup();"
        "from django.conf import settings as s;"
        "print(s.DEFAULT_FROM_EMAIL, s.EMAIL_HOST, s.EMAIL_PORT, s.EMAIL_HOST_USER,"
        " s.EMAIL_HOST_PASSWORD, s.EMAIL_USE_SSL, s.EMAIL_USE_TLS, s.EMAIL_TIMEOUT)"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == [
        "website@hanz.jsmx.org",
        "smtp.resend.com",
        "465",
        "resend",
        "re_123",
        "True",
        "False",
        "15",
    ]


def test_the_deployment_does_not_use_the_local_smoke_settings():
    """local_prod relaxes the TLS redirect, so it must never reach the server."""
    for path in (BASE_DIR / "prod").rglob("*"):
        if path.is_file():
            assert "local_prod" not in path.read_text(errors="ignore"), path
