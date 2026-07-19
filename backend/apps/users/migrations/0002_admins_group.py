
from django.db import migrations

GROUP_NAME = "admins"


def create_admins_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.get_or_create(name=GROUP_NAME)


def remove_admins_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_admins_group, remove_admins_group),
    ]
