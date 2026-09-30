import uuid
from django.db import models
from wagtail.models import Page
from wagtailseo.models import SeoMixin
from wagtailcache.cache import WagtailCacheMixin


class BasePage(WagtailCacheMixin, SeoMixin, Page):
    """
    Abstract base page model that defines common fields and
    functionality that should be shared across all page types.
    Inherits from SeoMixin to provide SEO functionality via wagtail-seo.
    """

    cache_control = "public, max-age=300, stale-while-revalidate=60"

    # Add a UUID field to provide a stable identifier for all page types
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Make this an abstract model
    class Meta:
        abstract = True

    # SEO settings specific to this project
    # We're using the SeoMixin from wagtail-seo which provides:
    # - seo_title (inherits from Wagtail Page)
    # - search_description (inherits from Wagtail Page)
    # - canonical_url
    # - og_image
    # Plus structured data, social meta tags, etc.

    # Panels - the promote tab is owned by wagtail-seo
    content_panels = Page.content_panels
    promote_panels = SeoMixin.seo_meta_panels
    settings_panels = Page.settings_panels
