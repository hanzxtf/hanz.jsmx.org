import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from wagtail.models import Site


@pytest.fixture(scope="session", autouse=True)
def static_root(tmp_path_factory):
    """
    WhiteNoise serves static files under uvicorn in development and warns on
    every request when STATIC_ROOT is missing. Give it a throwaway directory
    instead of leaving a stray one in the working tree.
    """
    settings.STATIC_ROOT = str(tmp_path_factory.mktemp("staticfiles"))


@pytest.fixture(scope="session", autouse=True)
def media_root(tmp_path_factory):
    """Keep the sample image and its renditions out of the working tree."""
    settings.MEDIA_ROOT = str(tmp_path_factory.mktemp("media"))


@pytest.fixture
def seeded_home(db):
    """The sample site, built by the same command developers run."""
    call_command("seed_demo", verbosity=0)
    return Site.objects.get(is_default_site=True).root_page


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="pw12345!"
    )
    client = Client()
    client.force_login(user)
    return client
