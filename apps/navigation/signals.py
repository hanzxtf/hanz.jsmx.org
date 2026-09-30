from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Menu, MenuItem, menu_tree_cache_key


def _invalidate(slug):
    if slug:
        cache.delete(menu_tree_cache_key(slug))


@receiver(post_save, sender=Menu)
@receiver(post_delete, sender=Menu)
def invalidate_menu_tree(sender, instance, **kwargs):
    _invalidate(instance.slug)


@receiver(post_save, sender=MenuItem)
@receiver(post_delete, sender=MenuItem)
def invalidate_parent_menu_tree(sender, instance, **kwargs):
    try:
        slug = instance.menu.slug
    except Menu.DoesNotExist:
        return
    _invalidate(slug)
