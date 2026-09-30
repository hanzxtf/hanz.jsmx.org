"""Entity pages are served at their slug URL, with no unserved URL variants."""

import pytest
from django.test import Client
from wagtail.models import Site

from apps.pages.models import FlexPage, ProjectPage, ProjectShowcasePage


@pytest.fixture
def project(db):
    home = Site.objects.get(is_default_site=True).root_page
    showcase = ProjectShowcasePage(title="Work", slug="work")
    home.add_child(instance=showcase)
    project = ProjectPage(title="Blue Whale", slug="blue-whale")
    showcase.add_child(instance=project)
    return project


@pytest.mark.django_db
def test_entity_page_is_served_at_its_slug_url(project):
    expected = "/work/blue-whale/"

    assert project.url == expected
    assert Client().get(expected).status_code == 200


def test_entity_page_has_no_url_type_switch():
    assert not hasattr(ProjectPage, "url_type_preference")


@pytest.mark.django_db
def test_project_page_links_to_its_child_pages(project):
    child = FlexPage(title="Blue Whale Details", slug="blue-whale-details")
    project.add_child(instance=child)

    response = Client().get(project.url)

    assert response.status_code == 200
    assert b"Blue Whale Details" in response.content


def test_project_page_has_no_has_page_switch():
    assert not hasattr(ProjectPage, "has_page")
