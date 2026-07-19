import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Intent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phrase", models.CharField(max_length=255)),
                (
                    "target",
                    models.CharField(
                        max_length=255,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="target must be a path-relative string starting with '/' (no absolute URLs)",
                                regex="^/(?!/)[A-Za-z0-9\\-_/]*$",
                            )
                        ],
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("navigate", "navigate"), ("confirm", "confirm")],
                        default="navigate",
                        max_length=16,
                    ),
                ),
                ("order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="auth.group",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "pk"],
            },
        ),
        migrations.CreateModel(
            name="IntentQuery",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("utterance", models.TextField(blank=True, null=True)),
                ("menu_offered", models.JSONField(default=list)),
                ("choice", models.CharField(max_length=255)),
                ("model_id", models.CharField(blank=True, max_length=255)),
                ("latency_ms", models.FloatField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "pk"],
            },
        ),
    ]
