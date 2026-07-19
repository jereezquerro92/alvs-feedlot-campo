from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("router", "0003_ai_operators_group"),
    ]

    operations = [
        migrations.AlterField(
            model_name="intent",
            name="phrase",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AddConstraint(
            model_name="intent",
            constraint=models.CheckConstraint(
                condition=~models.Q(phrase__in=("NO_MATCH", "ESCALATE")),
                name="intent_phrase_not_reserved",
                violation_error_message="phrase must not be a reserved outcome (NO_MATCH, ESCALATE)",
            ),
        ),
    ]
