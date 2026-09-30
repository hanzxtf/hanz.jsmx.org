"""Production configuration must be durable and self-describing."""

import re
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
    ]:
        assert re.search(
            rf"^{name}=", text, re.M
        ), f"{name} is required by the settings but missing from .env.prod.example"
