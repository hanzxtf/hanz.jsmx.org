"""Menu edits must not be served from a stale cache."""

import pytest

from apps.navigation.models import Menu, MenuItem
from apps.navigation.templatetags.navigation_tags import get_menu_tree


def titles(slug):
    return [node["item"].title for node in get_menu_tree(slug)]


@pytest.fixture
def menu(db):
    return Menu.objects.get(slug="main-menu")


@pytest.mark.django_db
def test_new_menu_item_appears_immediately(menu):
    assert titles("main-menu") == []

    MenuItem.objects.create(menu=menu, link_title="First", sort_order=1)

    assert titles("main-menu") == ["First"]


@pytest.mark.django_db
def test_renamed_menu_item_appears_immediately(menu):
    item = MenuItem.objects.create(menu=menu, link_title="First", sort_order=1)
    assert titles("main-menu") == ["First"]

    item.link_title = "Renamed"
    item.save()

    assert titles("main-menu") == ["Renamed"]


@pytest.mark.django_db
def test_deleted_menu_item_disappears_immediately(menu):
    item = MenuItem.objects.create(menu=menu, link_title="First", sort_order=1)
    assert titles("main-menu") == ["First"]

    item.delete()

    assert titles("main-menu") == []


@pytest.mark.django_db
def test_menu_snippet_admin_edits_items(admin_client):
    response = admin_client.get("/admin/snippets/navigation/menu/add/")

    assert response.status_code == 200
    assert b"menu_items" in response.content


@pytest.mark.django_db
def test_menus_are_reachable_from_the_snippets_index(admin_client):
    sidebar = admin_client.get("/admin/").content
    index = admin_client.get("/admin/snippets/").content

    assert sidebar.count(b"/admin/snippets/") == 1
    assert b"/admin/snippets/navigation/menu/" in index
