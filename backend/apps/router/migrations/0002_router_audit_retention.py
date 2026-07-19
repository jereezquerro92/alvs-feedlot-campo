import django.db.models.deletion
from django.db import migrations, models


def seed_router_auditors_group(apps, schema_editor):
    """Create the "Router Auditors" group ([[CHATBOT]] — Retention, #65)."""
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name="Router Auditors")


def remove_router_auditors_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Router Auditors").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("router", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="intentquery",
            name="raw_model_output",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="intentquery",
            name="chosen_intent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="router.intent",
            ),
        ),
        migrations.RunPython(seed_router_auditors_group, remove_router_auditors_group),
    ]
