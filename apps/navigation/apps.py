import logging

from django.apps import AppConfig
from django.core.cache import cache
from django.db import transaction
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

DEFAULT_MENUS = {
    "main-menu": "Navbar Menu",
    "footer-menu": "Footer Menu",
    "legal-menu": "Legal Menu",
}


class NavigationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.navigation"

    def ready(self):
        from . import signals  # noqa: F401

        post_migrate.connect(self.create_default_menus, sender=self)

    def create_default_menus(self, **kwargs):
        """Create the menus the templates look up, so a fresh install renders."""
        from .models import Menu, menu_tree_cache_key

        try:
            with transaction.atomic():
                for slug, title in DEFAULT_MENUS.items():
                    Menu.objects.get_or_create(slug=slug, defaults={"title": title})
        except Exception as exc:
            # The tables may not exist yet on a first migrate; retry next time.
            logger.warning("Could not create default menus: %s", exc)
            return

        cache.delete_many([menu_tree_cache_key(slug) for slug in DEFAULT_MENUS])
