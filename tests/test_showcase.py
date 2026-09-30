"""Showcase pages group sections, items and links."""

import pytest
from django.test import Client
from wagtail.models import Site

from apps.pages import models
from apps.pages.models import (
    ProjectPage,
    ShowcaseItem,
    ShowcaseItemLink,
    ShowcasePage,
    ShowcaseSection,
)


@pytest.fixture
def showcase(db):
    home = Site.objects.get(is_default_site=True).root_page
    page = ShowcasePage(title="Work", slug="work", introduction="Selected work")
    home.add_child(instance=page)
    return page


@pytest.mark.django_db
def test_showcase_page_renders_sections_items_and_links(showcase):
    section = ShowcaseSection.objects.create(
        showcase_page=showcase, heading="Featured", description="Our best work"
    )
    item = ShowcaseItem.objects.create(
        section=section, title="Blue Whale", description="A project"
    )
    ShowcaseItemLink.objects.create(
        item=item, title="Case study", url="https://example.com"
    )

    response = Client().get(showcase.url)

    assert response.status_code == 200
    assert b"Selected work" in response.content
    assert b"Featured" in response.content
    assert b"Blue Whale" in response.content
    assert b"Case study" in response.content


@pytest.mark.django_db
def test_showcase_page_can_hold_entity_pages(showcase):
    project = ProjectPage(title="Blue Whale", slug="blue-whale")
    showcase.add_child(instance=project)

    assert project.url == "/work/blue-whale/"
    assert Client().get(project.url).status_code == 200


def test_per_entity_showcase_page_types_are_gone():
    for name in [
        "ProjectShowcasePage",
        "ServiceShowcasePage",
        "PortfolioShowcasePage",
        "ResourceShowcasePage",
    ]:
        assert not hasattr(models, name), f"{name} should have been collapsed"
