import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture(scope="session", autouse=True)
def static_root(tmp_path_factory):
    """
    WhiteNoise serves static files under uvicorn in development and warns on
    every request when STATIC_ROOT is missing. Give it a throwaway directory
    instead of leaving a stray one in the working tree.
    """
    settings.STATIC_ROOT = str(tmp_path_factory.mktemp("staticfiles"))


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="pw12345!"
    )
    client = Client()
    client.force_login(user)
    return client
