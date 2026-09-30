"""The interactivity stack is htmx 4: no Turbo code, config or bundle may remain."""

import json
from pathlib import Path

from django.conf import settings

BASE_DIR = Path(settings.BASE_DIR)
FRONTEND = BASE_DIR / "frontend"

# frontend/dist is the build output, asserted by its own test
IGNORED_DIRS = {"dist", "node_modules", "__pycache__", "staticfiles", ".venv"}

SOURCES = [
    BASE_DIR / "apps",
    BASE_DIR / "config",
    BASE_DIR / "templates",
    FRONTEND / "src",
    BASE_DIR / "README.md",
    BASE_DIR / "justfile",
    BASE_DIR / "pyproject.toml",
    FRONTEND / "package.json",
]


def iter_files(root):
    if root.is_file():
        yield root
        return

    for path in root.rglob("*"):
        if path.is_file() and not IGNORED_DIRS.intersection(path.parts):
            yield path


def built_bundle():
    manifest = json.loads((FRONTEND / "dist" / "manifest.json").read_text())
    return FRONTEND / "dist" / manifest["src/app/main.js"]["file"]


def test_turbo_is_not_a_frontend_dependency():
    package = json.loads((FRONTEND / "package.json").read_text())

    assert "@hotwired/turbo" not in package["dependencies"]
    assert package["dependencies"]["htmx.org"] == "4.0.0"


def test_no_turbo_left_in_sources():
    offenders = {
        str(path.relative_to(BASE_DIR))
        for root in SOURCES
        for path in iter_files(root)
        if "turbo" in path.read_text(errors="ignore").lower()
    }

    assert offenders == set()


def test_body_boost_uses_htmx_inheritance():
    body = (BASE_DIR / "templates" / "base.html").read_text()

    # htmx 4 does not inherit plain attributes, so the :inherited modifier is required
    assert 'hx-boost:inherited="true"' in body


def test_form_is_a_boosted_htmx_form():
    form = (BASE_DIR / "templates" / "forms" / "form.html").read_text()

    # a boosted form needs an explicit action, and htmx 4 disables by selector
    assert 'action="' in form
    assert 'hx-disable="find button"' in form


def test_built_bundle_ships_htmx_and_not_turbo():
    bundle = built_bundle().read_text(errors="ignore")

    assert "htmx" in bundle
    assert "turbo" not in bundle.lower()
