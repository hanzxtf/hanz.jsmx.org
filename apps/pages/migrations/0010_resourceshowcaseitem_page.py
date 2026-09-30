# The page column already exists in the database; this only aligns the model
# state with the field ResourceShowcaseItem inherits from AbstractShowcaseItem.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0009_remove_portfolioitempage_url_type_preference_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
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
            ],
        ),
    ]
