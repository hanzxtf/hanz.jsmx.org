# ResourceShowcaseItem inherits the page link from AbstractShowcaseItem but the
# column was never created, so the model and the schema disagreed.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0009_remove_portfolioitempage_url_type_preference_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="resourceshowcaseitem",
            name="page",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional page to link to",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="wagtailcore.page",
            ),
        ),
    ]
