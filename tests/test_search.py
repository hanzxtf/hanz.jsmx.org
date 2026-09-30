"""Site search must return results instead of raising a 500."""

import re

import pytest
from django.test import Client
from wagtail.models import Page, Site

from apps.pages.models import FlexPage


@pytest.mark.django_db
def test_search_with_query_finds_a_page():
    root = Page.objects.get(depth=1)
    page = FlexPage(title="Zebra Handbook", slug="zebra-handbook")
    root.add_child(instance=page)
    page.save_revision().publish()

    response = Client().get("/search/", {"query": "Zebra"})

    assert response.status_code == 200
    assert b"Zebra Handbook" in response.content


@pytest.mark.django_db
def test_search_pagination_keeps_the_query():
    home = Site.objects.get(is_default_site=True).root_page
    for index in range(11):
        page = FlexPage(title=f"Zebra one {index}", slug=f"zebra-one-{index}")
        home.add_child(instance=page)

    response = Client().get("/search/", {"query": "Zebra one", "page": 2})

    assert response.status_code == 200
    links = re.findall(rb'href="([^"]*query[^"]*)"', response.content)
    assert links, "pagination links are missing"
    assert all(b" " not in link for link in links), "query is not url encoded"
    assert any(b"Zebra" in link for link in links), "query is lost from pagination"
