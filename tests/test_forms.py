"""Form pages are served by Wagtail, store submissions, and send mail."""

import pytest
from django.core import mail
from django.test import Client
from wagtail.models import Site

from apps.forms.models import FormPage


@pytest.fixture
def form_page(db):
    home = Site.objects.get(is_default_site=True).root_page
    page = FormPage(
        title="Contact",
        slug="contact",
        to_address="inbox@example.com",
        from_address="noreply@example.com",
        subject="New contact",
    )
    home.add_child(instance=page)
    return page


@pytest.mark.django_db
def test_form_page_is_served_at_its_url(form_page):
    assert form_page.url == "/contact/"
    assert Client().get("/contact/").status_code == 200


@pytest.mark.django_db
def test_draft_form_page_is_not_served(form_page):
    form_page.live = False
    form_page.save()

    assert Client().get("/contact/").status_code == 404


@pytest.mark.django_db
def test_submission_is_stored(form_page):
    Client().post("/contact/", {})

    submissions = form_page.get_submission_class().objects.filter(page=form_page)
    assert submissions.count() == 1


@pytest.mark.django_db
def test_submission_is_emailed(form_page):
    Client().post("/contact/", {})

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["inbox@example.com"]
    assert mail.outbox[0].from_email == "noreply@example.com"
    assert mail.outbox[0].subject == "New contact"


@pytest.mark.django_db
def test_submission_without_recipient_sends_no_mail(form_page):
    form_page.to_address = ""
    form_page.save()

    Client().post("/contact/", {})

    assert mail.outbox == []


@pytest.mark.django_db
def test_submission_survives_a_mail_server_that_is_down(form_page, monkeypatch, caplog):
    """The submission is stored, so a mail outage must not 500 the visitor."""

    def refuse(*args, **kwargs):
        raise ConnectionRefusedError("no mail server here")

    monkeypatch.setattr("apps.forms.models.send_mail", refuse)

    response = Client().post("/contact/", {})

    assert response.status_code == 200
    assert form_page.get_submission_class().objects.filter(page=form_page).count() == 1
    assert "Could not email the submission" in caplog.text


@pytest.mark.django_db
def test_legacy_uuid_form_route_is_gone(form_page):
    assert Client().get(f"/forms/{form_page.uuid}/").status_code == 404
