"""Smoke tests for the site shell: templates, homepage and search."""

import glob
import os

import pytest
from django.conf import settings
from django.template.loader import get_template
from django.test import Client

TEMPLATE_ROOT = os.path.join(settings.BASE_DIR, "templates")


def template_names():
    pattern = os.path.join(TEMPLATE_ROOT, "**", "*.html")
    for path in sorted(glob.glob(pattern, recursive=True)):
        yield os.path.relpath(path, TEMPLATE_ROOT)


def test_all_templates_compile():
    broken = {}
    for name in template_names():
        try:
            get_template(name)
        except Exception as exc:
            broken[name] = exc

    assert broken == {}


@pytest.mark.django_db
def test_homepage_renders():
    assert Client().get("/").status_code == 200


@pytest.mark.django_db
def test_search_page_renders():
    assert Client().get("/search/").status_code == 200
