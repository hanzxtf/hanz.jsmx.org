"""Site search must return results instead of raising a 500."""

import pytest
from django.test import Client
from wagtail.models import Page

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
