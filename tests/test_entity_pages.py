"""Entity pages are served at their slug URL, with no unserved URL variants."""

import pytest
from django.test import Client
from wagtail.models import Site

from apps.pages.models import ProjectPage, ProjectShowcasePage


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
