
from django.db import migrations

GROUP_NAME = "ai_operators"


def create_ai_operators_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name=GROUP_NAME)


def remove_ai_operators_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("router", "0002_router_audit_retention"),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_ai_operators_group, remove_ai_operators_group),
    ]
