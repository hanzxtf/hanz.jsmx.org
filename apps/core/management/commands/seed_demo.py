"""Create sample content covering every page type, block and site feature."""

import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.images import get_image_model
from wagtail.models import Page, Site

from apps.forms.models import FormPage
from apps.navigation.models import Menu, MenuItem
from apps.pages.models import (
    FlexPage,
    PortfolioItemPage,
    ProjectPage,
    ServicePage,
    ShowcaseItem,
    ShowcaseItemLink,
    ShowcasePage,
    ShowcaseSection,
    Tag,
)
from apps.settings.models import SiteSettings
from apps.snippets.models import Cta, Faq, TeamMember, Testimonial

# 1x1 transparent PNG, so image blocks and renditions are exercised as well
SAMPLE_IMAGE = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


class Command(BaseCommand):
    help = (
        "Create sample content: every page type, every block type, menus, a form, "
        "a showcase and the site settings. Safe to run more than once. With "
        "--clear it removes that content again."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove the sample content instead of creating it.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            return self.clear()

        home = self.home_page()
        # home_page may have replaced the site along with the placeholder page
        site = self.site()
        image = self.image()

        testimonial = self.testimonial(image)
        member = self.team_member(image)
        faq = self.faq()
        cta = self.cta()

        home.search_description = "Sample home page for local development."
        home.body = self.home_blocks(image, testimonial, member, faq, cta)
        home.save()

        about = self.page(
            home,
            FlexPage,
            "about",
            title="About",
            search_description="Who we are.",
            body=[
                ("heading", {"heading_text": "About us", "size": "h2"}),
                ("paragraph", "<p>Sample content for the about page.</p>"),
                (
                    "quote",
                    {"quote": "We ship small, boring sites.", "author": "The team"},
                ),
                ("team_member", {"team_member": member}),
                ("faq", {"faq": faq}),
            ],
        )

        work = self.page(
            home,
            ShowcasePage,
            "work",
            title="Work",
            search_description="Selected client work and products.",
            introduction="Selected client work and products.",
        )

        contact = self.page(
            home,
            FormPage,
            "contact",
            title="Contact",
            search_description="Tell us what you are building.",
            to_address="hello@example.com",
            from_address="noreply@example.com",
            subject="New contact form submission",
            thank_you_text="<p>Thanks, your message is on its way.</p>",
            body=[("heading", {"heading_text": "Say hello", "size": "h2"})],
            form_fields=[
                (
                    "char",
                    {
                        "field_label": "Name",
                        "help_text": "",
                        "required": True,
                        "format": "",
                        "default_value": "",
                    },
                ),
                (
                    "char",
                    {
                        "field_label": "Email",
                        "help_text": "Never shared.",
                        "required": True,
                        "format": "email",
                        "default_value": "",
                    },
                ),
                (
                    "text",
                    {"field_label": "Message", "help_text": "", "required": True},
                ),
                (
                    "dropdown",
                    {
                        "field_label": "Topic",
                        "help_text": "",
                        "required": False,
                        "choices": ["New project", "Support"],
                    },
                ),
                (
                    "checkbox",
                    {
                        "field_label": "Subscribe to the newsletter",
                        "help_text": "",
                        "default_value": False,
                    },
                ),
            ],
        )

        project = self.page(
            work,
            ProjectPage,
            "blue-whale",
            title="Blue Whale",
            tag=self.tag("Case study"),
            body=[
                ("heading", {"heading_text": "Blue Whale", "size": "h2"}),
                ("paragraph", "<p>A migration from a legacy CMS.</p>"),
            ],
        )
        self.page(
            project,
            FlexPage,
            "blue-whale-results",
            title="Blue Whale results",
            body=[("paragraph", "<p>Load times dropped by half.</p>")],
        )

        service = self.page(
            work,
            ServicePage,
            "support-plan",
            title="Support plan",
            tag=self.tag("Product"),
            body=[("paragraph", "<p>Monthly maintenance and updates.</p>")],
        )

        portfolio = self.page(
            work,
            PortfolioItemPage,
            "field-notes",
            title="Field Notes",
            tag=self.tag("Product"),
            image=image,
            body=[("paragraph", "<p>A writing app for researchers.</p>")],
        )

        self.showcase_sections(work, project, service, portfolio)
        self.menus(home, work, about, contact)
        self.settings(site, image)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Page.objects.count()} pages, {Page.objects.live().count()} of them live."
            )
        )

    def clear(self):
        """Remove the sample content, leaving an empty site that still serves."""
        home = self.site().root_page.specific

        if not isinstance(home, FlexPage):
            self.stdout.write(
                "Nothing to clear: the site is not running the sample home page."
            )
            return

        # delete through the queryset, then resync the count treebeard keeps on the
        # parent: deleting a page outside the admin leaves that count stale
        home.get_children().filter(slug__in=["about", "work", "contact"]).delete()
        self.sync_numchild(home)

        home.body = []
        home.search_description = ""
        home.save()

        Testimonial.objects.filter(author="Ada Sample").delete()
        TeamMember.objects.filter(name="Grace Sample").delete()
        Faq.objects.filter(question="What is this?").delete()
        Cta.objects.filter(title="Start a project").delete()
        Tag.objects.filter(name__in=["Case study", "Product"]).delete()
        MenuItem.objects.filter(link_url="https://example.com/docs").delete()
        MenuItem.objects.filter(
            menu__slug__in=["main-menu", "footer-menu"], link_page=home
        ).delete()

        settings = SiteSettings.for_site(self.site())
        for field in (
            "site_title",
            "site_description",
            "contact_email",
            "contact_phone",
            "address",
        ):
            setattr(settings, field, "")
        settings.site_logo = None
        settings.save()

        get_image_model().objects.filter(title="Sample image").delete()

        self.stdout.write(self.style.SUCCESS("Removed the sample content."))

    def sync_numchild(self, page):
        """Recount a page's children so treebeard's cached count cannot drift."""
        page.numchild = page.get_children().count()
        Page.objects.filter(pk=page.pk).update(numchild=page.numchild)
        return page

    def site(self):
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            site = Site.objects.first()
        if site is None:
            raise CommandError("No Wagtail site found. Run `manage.py migrate` first.")
        return site

    def home_page(self):
        """Return the site's home page, replacing Wagtail's placeholder if needed."""
        site = self.site()
        root = Page.get_first_root_node()
        home = root.get_children().filter(slug="home").first()

        if home is not None and isinstance(home.specific, FlexPage):
            return home.specific

        if home is not None and home.get_children().exists():
            raise CommandError(
                f"Refusing to replace {home!r}: it has child pages. "
                "Seed a database without content, or delete those pages first."
            )

        hostname, port, site_name = site.hostname, site.port, site.site_name
        site.delete()
        if home is not None:
            root.get_children().filter(slug="home").delete()

        # treebeard picks its insert branch from the cached child count
        self.sync_numchild(root)
        home = FlexPage(title="Home", slug="home")
        root.add_child(instance=home)
        Site.objects.create(
            hostname=hostname,
            port=port,
            site_name=site_name,
            root_page=home,
            is_default_site=True,
        )
        self.stdout.write(f"Replaced the placeholder home page with {home!r}.")
        return home

    def page(self, parent, model, slug, **fields):
        """Get or create a live child page with this slug, updating its fields."""
        page = parent.get_children().filter(slug=slug).specific().first()

        if page is None:
            page = model(slug=slug, **fields)
            parent.add_child(instance=page)
            return page

        for name, value in fields.items():
            setattr(page, name, value)
        page.save()
        return page

    def image(self):
        Image = get_image_model()
        image = Image.objects.filter(title="Sample image").first()
        if image is not None:
            return image
        return Image.objects.create(
            title="Sample image",
            file=ContentFile(SAMPLE_IMAGE, name="sample.png"),
        )

    def tag(self, name):
        tag, _ = Tag.objects.get_or_create(name=name)
        return tag

    def testimonial(self, image):
        testimonial, _ = Testimonial.objects.update_or_create(
            author="Ada Sample",
            defaults={"quote": "The sample data finally works.", "image": image},
        )
        return testimonial

    def team_member(self, image):
        member, _ = TeamMember.objects.update_or_create(
            name="Grace Sample",
            defaults={"role": "Lead Developer", "photo": image},
        )
        return member

    def faq(self):
        faq, _ = Faq.objects.update_or_create(
            question="What is this?",
            defaults={"answer": "Sample content.", "category": "general"},
        )
        return faq

    def cta(self):
        cta, _ = Cta.objects.update_or_create(
            title="Start a project",
            defaults={
                "description": "Tell us what you are building.",
                "button_text": "Get in touch",
                "button_url": "https://example.com/contact",
                "style": "primary",
            },
        )
        return cta

    def home_blocks(self, image, testimonial, member, faq, cta):
        """Every block type in ContentStreamBlock, so one page renders them all."""
        return [
            (
                "hero",
                [
                    (
                        "simple_hero",
                        {
                            "title": "Sample marketing site",
                            "subtitle": "Every block, on one page.",
                            "cta_button_text": "Read the docs",
                            "cta_button_link": "https://example.com/docs",
                        },
                    )
                ],
            ),
            ("heading", {"heading_text": "Sample heading", "size": "h2"}),
            ("paragraph", "<p>Sample paragraph with <strong>rich text</strong>.</p>"),
            (
                "two_column",
                {
                    "left_column": [("paragraph", "<p>Left column.</p>")],
                    "right_column": [
                        ("quote", {"quote": "Right column.", "author": "The team"})
                    ],
                },
            ),
            (
                "three_column",
                {
                    "left_column": [("heading", {"heading_text": "Column one"})],
                    "middle_column": [("heading", {"heading_text": "Column two"})],
                    "right_column": [("heading", {"heading_text": "Column three"})],
                },
            ),
            (
                "card",
                {
                    "title": "Sample card",
                    "text": "<p>Card body copy.</p>",
                    "image": image,
                    "link": "https://example.com/card",
                    "link_text": "Open",
                },
            ),
            (
                "image",
                {
                    "image": image,
                    "caption": "Sample caption",
                    "attribution": "Sample attribution",
                },
            ),
            ("quote", {"quote": "Sample quote.", "author": "A. Editor"}),
            (
                "button",
                {
                    "button_text": "Sample button",
                    "link": "https://example.com/button",
                    "style": "primary",
                },
            ),
            (
                "cta",
                {
                    "title": "Sample call to action",
                    "text": "<p>Call to action copy.</p>",
                    "button_text": "Go",
                    "button_link": "https://example.com/cta",
                },
            ),
            (
                "slider",
                {
                    "slides": [
                        ("paragraph", "<p>Slide one.</p>"),
                        ("paragraph", "<p>Slide two.</p>"),
                    ]
                },
            ),
            (
                "marquee",
                {
                    "items": [
                        ("heading", {"heading_text": "Marquee one"}),
                        ("heading", {"heading_text": "Marquee two"}),
                    ]
                },
            ),
            (
                "table",
                {
                    "table_header": ["Plan", "Price"],
                    "table_body": [["Basic", "$9"], ["Pro", "$29"]],
                },
            ),
            ("testimonial", {"testimonial": testimonial}),
            ("team_member", {"team_member": member}),
            ("faq", {"faq": faq}),
            ("cta_snippet", {"cta": cta}),
        ]

    def showcase_sections(self, work, project, service, portfolio):
        client_work = self.section(work, "Client work", "Recent projects.", 1)
        products = self.section(work, "Products", "Things we build.", 2)

        self.item(client_work, "Blue Whale", "A legacy migration.", project, 1)
        self.item(client_work, "Field Notes", "A writing app.", portfolio, 2)
        self.item(products, "Support plan", "Monthly maintenance.", service, 3)

    def section(self, work, heading, description, sort_order):
        section, _ = ShowcaseSection.objects.update_or_create(
            showcase_page=work,
            heading=heading,
            defaults={"description": description, "sort_order": sort_order},
        )
        return section

    def item(self, section, title, description, page, sort_order):
        item, _ = ShowcaseItem.objects.update_or_create(
            section=section,
            title=title,
            defaults={
                "description": description,
                "page": page,
                "sort_order": sort_order,
            },
        )
        ShowcaseItemLink.objects.update_or_create(
            item=item,
            title=f"{title} case study",
            defaults={"url": "https://example.com/case-study", "target": "_blank"},
        )
        return item

    def menus(self, home, work, about, contact):
        main = Menu.objects.get(slug="main-menu")
        footer = Menu.objects.get(slug="footer-menu")

        home_item = self.menu_item(main, "Home", 1, link_page=home)
        work_item = self.menu_item(main, "Work", 2, link_page=work)
        self.menu_item(main, "About", 1, parent=work_item, link_page=about)
        self.menu_item(main, "Contact", 3, link_page=contact)
        self.menu_item(
            main,
            "Docs",
            4,
            link_url="https://example.com/docs",
            open_in_new_tab=True,
        )

        self.menu_item(footer, "Home", 1, link_page=home)
        self.menu_item(footer, "About", 2, link_page=about)
        self.menu_item(footer, "Contact", 3, link_page=contact)
        return home_item

    def menu_item(self, menu, title, sort_order, parent=None, link_page=None, **fields):
        item, _ = MenuItem.objects.update_or_create(
            menu=menu,
            link_title=title,
            parent=parent,
            defaults={
                "sort_order": sort_order,
                "link_page": link_page,
                **fields,
            },
        )
        return item

    def settings(self, site, image):
        settings = SiteSettings.for_site(site)
        settings.site_title = "Sample Site"
        settings.site_description = "Sample content for local development."
        settings.contact_email = "hello@example.com"
        settings.contact_phone = "+1 555 0100"
        settings.address = "1 Sample Street"
        settings.site_logo = image
        settings.save()
        return settings
