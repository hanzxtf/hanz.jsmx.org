from django.db import models
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from apps.core.models import BasePage
from apps.blocks.models import ContentStreamBlock


class FlexPage(BasePage):
    """
    A flexible page model that can be used for the homepage or other standard pages.
    It uses a StreamField for maximum content flexibility.
    """

    # Main content area as a StreamField for flexible content
    body = StreamField(
        ContentStreamBlock(),
        use_json_field=True,
        blank=True,
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = BasePage.promote_panels
    settings_panels = BasePage.settings_panels

    # Allow only one instance at the root level
    parent_page_types = ["wagtailcore.Page", "pages.FlexPage"]

    # Specify the template for this page
    template = "pages/flex_page.html"

    class Meta:
        verbose_name = "Flex Page"
        verbose_name_plural = "Flex Pages"


@register_snippet
class Tag(models.Model):
    """
    A tag for organizing and filtering showcase entities.
    Tags can be assigned to any BaseEntityPage to categorize content.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]


class BaseEntityPage(FlexPage):
    """
    Abstract base page for all showcase entities with common fields.
    Entities can be tagged with a Tag for organization and filtering.
    This model provides common functionality for all showcase entity types.
    """

    tag = models.ForeignKey(
        "pages.Tag",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    # Add tag to content panels
    content_panels = FlexPage.content_panels + [
        FieldPanel("tag"),
    ]

    template = "pages/entity_base.html"

    class Meta:
        abstract = True


class ProjectPage(BaseEntityPage):
    """
    A project page that may or may not have child pages.
    """

    content_panels = BaseEntityPage.content_panels

    parent_page_types = ["pages.ShowcasePage"]
    subpage_types = ["pages.FlexPage"]
    template = "pages/project_page.html"

    class Meta:
        verbose_name = "Project Page"
        verbose_name_plural = "Project Pages"


class ServicePage(BaseEntityPage):
    """
    A service page that always has child pages.
    """

    content_panels = (
        BaseEntityPage.content_panels
        + [
            # Services typically don't have links in list view, but you can add them here if needed
        ]
    )

    parent_page_types = ["pages.ShowcasePage"]
    subpage_types = ["pages.FlexPage"]
    template = "pages/service_page.html"

    def save(self, *args, **kwargs):
        # Services always have pages, so we don't need to modify subpage_types
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Service Page"
        verbose_name_plural = "Service Pages"


class PortfolioItemPage(BaseEntityPage):
    """
    A portfolio item page that always has child pages and includes an image.
    """

    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    content_panels = BaseEntityPage.content_panels + [
        FieldPanel("image"),
    ]

    parent_page_types = ["pages.ShowcasePage"]
    subpage_types = ["pages.FlexPage"]
    template = "pages/portfolio_item_page.html"

    class Meta:
        verbose_name = "Portfolio Item Page"
        verbose_name_plural = "Portfolio Item Pages"


class ShowcasePage(BasePage):
    """
    A page that showcases a collection of entities, grouped into sections.
    Editors assign items to each section explicitly.
    """

    # Introduction text for the page
    introduction = models.TextField(
        blank=True, help_text="Optional introduction text for the showcase page"
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("introduction"),
        InlinePanel(
            "showcase_sections",
            label="Sections",
            help_text="Add and order sections to display on this page",
        ),
    ]

    template = "pages/showcase_page.html"
    parent_page_types = ["wagtailcore.Page", "pages.FlexPage"]
    subpage_types = [
        "pages.ProjectPage",
        "pages.ServicePage",
        "pages.PortfolioItemPage",
    ]

    class Meta:
        verbose_name = "Showcase Page"
        verbose_name_plural = "Showcase Pages"


class ShowcaseSection(ClusterableModel, Orderable):
    """
    A section on a showcase page, holding explicitly assigned items.
    """

    heading = models.CharField(max_length=200, help_text="Heading for this section")
    description = models.TextField(
        blank=True, help_text="Optional description for this section"
    )
    showcase_page = ParentalKey(
        "pages.ShowcasePage",
        on_delete=models.CASCADE,
        related_name="showcase_sections",
    )

    panels = [
        FieldPanel("heading"),
        FieldPanel("description"),
        InlinePanel("items", label="Items", help_text="Add items to this section"),
    ]

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.showcase_page.title} -> {self.heading}"

    def get_items(self):
        """
        Get items explicitly assigned to this section.
        """
        return self.items.all()


class ShowcaseItem(ClusterableModel, Orderable):
    """
    An item in a showcase section, with its own title, description and links.
    """

    title = models.CharField(
        max_length=200, help_text="Title for this item", default="Untitled"
    )
    description = models.TextField(blank=True, help_text="Description for this item")

    # Optional page reference
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional page to link to",
    )
    section = ParentalKey(
        "pages.ShowcaseSection", on_delete=models.CASCADE, related_name="items"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("description"),
        FieldPanel("page"),
        InlinePanel("links", label="Links", help_text="Links for this item"),
    ]

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.section.heading} -> {self.title}"

    def get_links(self):
        """
        Get links for this item.
        """
        return self.links.all()


class ShowcaseItemLink(Orderable):
    """
    A link attached to a showcase item.
    """

    LINK_TARGET_CHOICES = [
        ("_self", "Same Window"),
        ("_blank", "New Window"),
    ]

    title = models.CharField(max_length=200)
    url = models.URLField()
    target = models.CharField(
        max_length=10, choices=LINK_TARGET_CHOICES, default="_self"
    )
    item = ParentalKey(
        "pages.ShowcaseItem", on_delete=models.CASCADE, related_name="links"
    )

    panels = [
        FieldPanel("title"),
        FieldPanel("url"),
        FieldPanel("target"),
    ]

    class Meta:
        ordering = ["sort_order"]

    def __str__(self):
        return f"{self.item.title} -> {self.title}"
