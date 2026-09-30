"""Model state must always be captured by a migration."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_no_missing_migrations():
    try:
        call_command(
            "makemigrations",
            "--check",
            "--dry-run",
            verbosity=0,
            stdout=StringIO(),
        )
    except (SystemExit, CommandError):
        pytest.fail("model changes exist that no migration captures")
