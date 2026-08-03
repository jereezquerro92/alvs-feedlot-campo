# Seed the feed catalog with the common cattle feeds (task #25). FeedType is an
# editable catalog (adr-49 rule 3), so this only fills in rows an operator would
# otherwise create by hand; it is idempotent (get_or_create by unique name) and
# reversible to a no-op. Names are rendered data (Spanish is allowed for data,
# LOCALIZATION only binds code/keys).

from django.db import migrations

# (name, category) — categories mirror the ones already in use.
FEED_TYPES = [
    ("Alfalfa", "forraje"),
    ("Picado de alfalfa", "voluminoso"),
    ("Picado de maíz", "voluminoso"),
    ("Rollo de alfalfa", "voluminoso"),
    ("Silaje de sorgo", "voluminoso"),
    ("Centeno", "verdeo"),
    ("Avena", "verdeo"),
    ("Grano de maíz", "grano"),
    ("Grano de sorgo", "grano"),
    ("Grano de cebada", "grano"),
    ("Expeller de soja", "proteico"),
    ("Pellet de alfalfa", "proteico"),
    ("Cascarilla de soja", "subproducto"),
    ("Afrechillo de trigo", "subproducto"),
    ("Burlanda de maíz", "subproducto"),
    ("Núcleo vitamínico mineral", "aditivo"),
    ("Urea", "aditivo"),
]


def seed(apps, schema_editor):
    FeedType = apps.get_model("feed", "FeedType")
    for name, category in FEED_TYPES:
        FeedType.objects.get_or_create(name=name, defaults={"category": category})


def unseed(apps, schema_editor):
    # Reverse is a no-op: an operator may have started using these rows, and a
    # FeedType referenced by a movement/feeding is PROTECTed. Leave them.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0002_feedingevent_pen"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
