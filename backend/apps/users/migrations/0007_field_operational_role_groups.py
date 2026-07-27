"""Create the six field-operational role Groups (adr-44).

Same idempotent get_or_create pattern as 0002_admins_group; each role is a
Django auth.Group and RBAC reads membership only (adr-10 rule 2).
"""

from django.db import migrations

ROLE_GROUPS = (
    "field_managers",
    "feed_operators",
    "lot_owners",
    "field_admins",
    "feedlot_owners",
    "workshop",
)


def create_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in ROLE_GROUPS:
        Group.objects.get_or_create(name=name)


def remove_role_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_accessrequest"),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_role_groups, remove_role_groups),
    ]
