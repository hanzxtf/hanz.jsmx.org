import logging
from django import template
from django.core.cache import cache
from apps.navigation.models import Menu

logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def get_menu_tree(slug):
    """
    Returns the complete menu tree with nested structure for the given slug.
    Includes caching for performance optimization.
    """
    # Try to get from cache first
    cache_key = f"menu_tree_{slug}"
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        return cached_result

    try:
        # Get menu with prefetched items
        menu = Menu.objects.prefetch_related(
            "menu_items__link_page", "menu_items__children__link_page"
        ).get(slug=slug)
        result = menu.get_menu_tree()

        # Cache for 15 minutes (adjust as needed)
        cache.set(cache_key, result, 900)
        return result
    except Menu.DoesNotExist:
        logger.warning(f"Menu with slug '{slug}' does not exist")
        return []
    except Exception as e:
        logger.error(f"Error retrieving menu tree for slug '{slug}': {str(e)}")
        return []
