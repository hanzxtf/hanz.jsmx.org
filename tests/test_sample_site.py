"""Sample data covers every page type, block and visitor-facing feature."""

import re

import pytest
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from apps.navigation.models import MenuItem
from apps.pages.models import (
    FlexPage,
    PortfolioItemPage,
    ProjectPage,
    ServicePage,
    ShowcasePage,
    Tag,
)
from apps.snippets.models import TeamMember

PAGE_TYPES = [
    FlexPage,
    ShowcasePage,
    ProjectPage,
    ServicePage,
    PortfolioItemPage,
]

# one marker per block in ContentStreamBlock
BLOCK_MARKERS = [
    "Sample marketing site",  # hero > simple_hero
    "Sample heading",  # heading
    "Sample paragraph with",  # paragraph
    "Left column",  # two_column
    "Column two",  # three_column
    "Sample card",  # card
    "Sample caption",  # image
    "Sample quote.",  # quote
    "Sample button",  # button
    "Sample call to action",  # cta
    "Slide two",  # slider
    "Marquee two",  # marquee
    "Basic",  # table
    "The sample data finally works.",  # testimonial snippet
    "Grace Sample",  # team member snippet
    "What is this?",  # faq snippet
    "Start a project",  # cta snippet
]


@pytest.mark.django_db
def test_seed_demo_is_idempotent(seeded_home):
    before = Page.objects.count()

    call_command("seed_demo", verbosity=0)

    assert Page.objects.count() == before
    assert Page.objects.live().count() == before


@pytest.mark.django_db
def test_seed_demo_clear_removes_the_sample_site(seeded_home):
    call_command("seed_demo", "--clear", verbosity=0)

    home = Site.objects.get(is_default_site=True).root_page
    assert Client().get("/").status_code == 200
    assert home.get_children().count() == 0
    assert not home.specific.body
    assert Tag.objects.count() == 0
    assert MenuItem.objects.count() == 0
    assert TeamMember.objects.count() == 0
    assert get_image_model().objects.count() == 0


@pytest.mark.django_db
def test_seed_demo_clear_leaves_a_healthy_page_tree(seeded_home):
    """treebeard counts children in numchild; a stale count breaks page creation."""
    call_command("seed_demo", "--clear", verbosity=0)

    home = Site.objects.get(is_default_site=True).root_page
    root = Page.get_first_root_node()

    assert Page.objects.get(pk=home.pk).numchild == home.get_children().count() == 0
    assert Page.objects.get(pk=root.pk).numchild == root.get_children().count() == 1

    # seeding the cleared site has to work again
    call_command("seed_demo", verbosity=0)
    assert Page.objects.count() == 9


@pytest.mark.django_db
def test_seed_demo_builds_one_page_of_every_type(seeded_home):
    seeded_types = {
        page.specific_class for page in seeded_home.get_descendants(inclusive=True)
    }

    for model in PAGE_TYPES:
        assert (
            model in seeded_types
        ), f"{model.__name__} is missing from the sample site"


@pytest.mark.django_db
def test_seed_demo_refuses_to_replace_a_home_page_that_has_children():
    """The placeholder home page is only replaced while the site is still empty."""
    home = Site.objects.get(is_default_site=True).root_page
    home.add_child(instance=Page(title="Existing", slug="existing"))

    with pytest.raises(CommandError, match="Refusing to replace"):
        call_command("seed_demo", verbosity=0)


@pytest.mark.django_db
def test_every_live_page_is_served(seeded_home):
    client = Client()
    pages = seeded_home.get_descendants(inclusive=True).live().public()

    assert pages.count() >= 8, "the sample site is too small to prove anything"

    for page in pages:
        url = page.get_url()
        assert url, f"{page!r} has no URL"

        response = client.get(url)
        assert response.status_code == 200, f"{url} -> {response.status_code}"

        html = response.content.decode()
        assert page.title in html, url
        if page.search_description:
            assert page.search_description in html, url


@pytest.mark.django_db
def test_every_page_carries_the_site_shell(seeded_home):
    client = Client()

    for page in seeded_home.get_descendants(inclusive=True).live():
        html = client.get(page.get_url()).content.decode()
        assert "<header" in html, page.slug
        assert "<footer" in html, page.slug
        assert "hx-boost:inherited" in html, page.slug


@pytest.mark.django_db
def test_home_page_renders_every_block_type(seeded_home):
    html = Client().get("/").content.decode()

    missing = [marker for marker in BLOCK_MARKERS if marker not in html]
    assert missing == []


@pytest.mark.django_db
def test_navigation_renders_the_seeded_menus(seeded_home):
    html = Client().get("/").content.decode()

    # leaf items link directly, the item with children renders as a dropdown
    assert 'href="/contact/"' in html
    assert 'href="https://example.com/docs"' in html
    assert 'target="_blank"' in html
    assert "<details>" in html

    work_at = html.find("Work")
    about_at = html.find('href="/about/"')
    assert work_at != -1 and about_at != -1
    assert work_at < about_at, "About should be nested inside the Work dropdown"


@pytest.mark.django_db
def test_showcase_page_lists_its_sections_items_and_links(seeded_home):
    html = Client().get("/work/").content.decode()

    for marker in [
        "Client work",
        "Products",
        "Blue Whale",
        "Field Notes",
        "Support plan",
        "Blue Whale case study",
    ]:
        assert marker in html, marker


@pytest.mark.django_db
def test_entity_pages_link_to_their_children(seeded_home):
    html = Client().get("/work/blue-whale/").content.decode()

    assert "Blue Whale results" in html
    assert 'href="/work/blue-whale/blue-whale-results/"' in html


@pytest.mark.django_db
def test_search_finds_seeded_pages(seeded_home):
    response = Client().get("/search/", {"query": "Blue"})

    assert response.status_code == 200
    assert "Blue Whale" in response.content.decode()


@pytest.mark.django_db
def test_contact_form_accepts_stores_and_emails_a_submission(seeded_home):
    contact = seeded_home.get_children().get(slug="contact").specific

    response = Client().post(
        "/contact/",
        {
            "name": "Ada Lovelace",
            "email": "ada@example.com",
            "message": "Please build me a site.",
            "topic": "New project",
        },
    )

    assert response.status_code == 200
    assert "Thanks, your message is on its way." in response.content.decode()
    assert contact.get_submission_class().objects.filter(page=contact).count() == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["hello@example.com"]
    assert "Please build me a site." in mail.outbox[0].body


@pytest.mark.django_db
def test_contact_form_shows_errors_instead_of_storing_incomplete_input(seeded_home):
    contact = seeded_home.get_children().get(slug="contact").specific

    response = Client().post("/contact/", {"name": "Ada Lovelace"})

    assert response.status_code == 200
    assert "This field is required." in response.content.decode()
    assert contact.get_submission_class().objects.count() == 0
    assert mail.outbox == []


@pytest.mark.django_db
def test_unknown_urls_are_404(seeded_home):
    assert Client().get("/no-such-page/").status_code == 404


@pytest.mark.django_db
def test_admin_needs_a_login(seeded_home):
    response = Client().get("/admin/")

    assert response.status_code == 302
    assert "login" in response["Location"]


@pytest.mark.django_db
def test_seeded_pages_are_reachable_from_the_sitemap_of_links(seeded_home):
    """Every internal href on the home page resolves."""
    client = Client()
    html = client.get("/").content.decode()

    hrefs = {
        href
        for href in re.findall(r'href="(/[^"#]*)"', html)
        if not href.startswith("/static/")
    }
    assert hrefs, "the home page links to nothing"

    for href in sorted(hrefs):
        assert client.get(href).status_code == 200, href


@pytest.mark.django_db
def test_only_one_default_site_exists(seeded_home):
    assert Site.objects.filter(is_default_site=True).count() == 1
