from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import Menu


class MenuAdmin(SnippetViewSet):
    model = Menu

    # Add search fields for better admin experience
    search_fields = ["title", "slug"]

    # Add list display for better overview
    list_display = ["title", "slug"]

    @property
    def icon(self):
        return "bars"

    @property
    def menu_label(self):
        return "Navigation Menus"

    @property
    def menu_name(self):
        return "navigation_menus"

    @property
    def menu_order(self):
        return 100


# Register the Menu model as a snippet with the custom admin interface
register_snippet(MenuAdmin)
