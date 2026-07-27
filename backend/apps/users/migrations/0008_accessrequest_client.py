"""Add AccessRequest.client — the per-client binding for lot_owners (adr-44 decision 4)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_field_operational_role_groups"),
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="accessrequest",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="access_requests",
                to="clients.client",
            ),
        ),
    ]
