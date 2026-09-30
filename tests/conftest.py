import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_superuser(
        username="admin", email="admin@example.com", password="pw12345!"
    )
    client = Client()
    client.force_login(user)
    return client
