# Generated manually for #61 — UniqueConstraint (site, date) for idempotent ingest.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("weather", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="weatherlog",
            constraint=models.UniqueConstraint(
                fields=("site", "date"),
                name="weather_log_site_date_uniq",
            ),
        ),
    ]
