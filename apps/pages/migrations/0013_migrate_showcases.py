# One-off migration: fold the four per-entity showcase page types into one
# ShowcasePage, carrying their sections, items and links across.
#
# Historical models have no treebeard or Wagtail page helpers, so each page is
# retyped in place: the wagtailcore_page row keeps its id, path, url_path and
# children, the old concrete row is dropped and the new one takes its place.
from django.db import migrations

FAMILIES = [
    (
        "ProjectShowcasePage",
        "ProjectShowcaseSection",
        "ProjectShowcaseItem",
        "ProjectShowcaseItemLink",
    ),
    (
        "ServiceShowcasePage",
        "ServiceShowcaseSection",
        "ServiceShowcaseItem",
        "ServiceShowcaseItemLink",
    ),
    (
        "PortfolioShowcasePage",
        "PortfolioShowcaseSection",
        "PortfolioShowcaseItem",
        "PortfolioShowcaseItemLink",
    ),
    (
        "ResourceShowcasePage",
        "ResourceShowcaseSection",
        "ResourceShowcaseItem",
        "ResourceShowcaseItemLink",
    ),
]


def migrate_showcases(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    ShowcasePage = apps.get_model("pages", "ShowcasePage")
    ShowcaseSection = apps.get_model("pages", "ShowcaseSection")
    ShowcaseItem = apps.get_model("pages", "ShowcaseItem")
    ShowcaseItemLink = apps.get_model("pages", "ShowcaseItemLink")

    db_alias = schema_editor.connection.alias
    cursor = schema_editor.connection.cursor()
    showcase_table = ShowcasePage._meta.db_table

    # Wagtail creates page content types in a post_migrate handler that has not
    # run yet, so make sure the row the retyped pages need exists.
    showcase_content_type, _ = ContentType.objects.using(db_alias).get_or_create(
        app_label="pages", model="showcasepage"
    )

    for page_model_name, section_name, item_name, link_name in FAMILIES:
        PageModel = apps.get_model("pages", page_model_name)
        SectionModel = apps.get_model("pages", section_name)
        ItemModel = apps.get_model("pages", item_name)
        LinkModel = apps.get_model("pages", link_name)

        for old in PageModel.objects.using(db_alias).all():
            # Inserted with SQL because multi-table inheritance would try to
            # create a second wagtailcore_page row for the same page.
            cursor.execute(
                f"insert into {showcase_table}"
                " (page_ptr_id, introduction, canonical_url, uuid)"
                " values (%s, %s, %s, %s)",
                (old.pk, old.introduction, old.canonical_url, old.uuid.hex),
            )

            for section in SectionModel.objects.using(db_alias).filter(
                showcase_page_id=old.pk
            ):
                new_section = ShowcaseSection.objects.using(db_alias).create(
                    showcase_page_id=old.pk,
                    heading=section.heading,
                    description=section.description,
                    sort_order=section.sort_order,
                )
                for item in ItemModel.objects.using(db_alias).filter(
                    section_id=section.pk
                ):
                    new_item = ShowcaseItem.objects.using(db_alias).create(
                        section=new_section,
                        title=item.title,
                        description=item.description,
                        page_id=item.page_id,
                        sort_order=item.sort_order,
                    )
                    for link in LinkModel.objects.using(db_alias).filter(
                        item_id=item.pk
                    ):
                        ShowcaseItemLink.objects.using(db_alias).create(
                            item=new_item,
                            title=link.title,
                            url=link.url,
                            target=link.target,
                            sort_order=link.sort_order,
                        )

            # Removes the old concrete row and, by cascade, its sections, items
            # and links, while keeping the page itself in the tree.
            old.delete(keep_parents=True)

            Page.objects.using(db_alias).filter(pk=old.pk).update(
                content_type_id=showcase_content_type.pk,
                latest_revision_id=None,
                live_revision_id=None,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0012_showcaseitem_showcaseitemlink_showcasepage_and_more"),
    ]

    operations = [migrations.RunPython(migrate_showcases, migrations.RunPython.noop)]
