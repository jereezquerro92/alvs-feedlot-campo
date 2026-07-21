"""Intake services — create cattle individually or as a lot (adr-26 rule 1)."""

from decimal import Decimal

from django.db import transaction

from apps.livestock.models import Animal, Intake, Lot


@transaction.atomic
def create_individual_intake(*, client, date, animals):
    """`animals`: list of dicts {ear_tag, category, sex?, entry_weight?}."""
    intake = Intake.objects.create(
        client=client, date=date, mode=Intake.Mode.INDIVIDUAL, head_count=len(animals)
    )
    created = []
    for a in animals:
        created.append(
            Animal.objects.create(
                client=client,
                ear_tag=a["ear_tag"],
                category=a["category"],
                sex=a.get("sex", ""),
                entry_date=date,
                entry_weight=a.get("entry_weight"),
                current_weight=a.get("entry_weight"),
            )
        )
    return intake, created


@transaction.atomic
def create_lot_intake(*, client, date, code, head_count, total_weight):
    lot = Lot.objects.create(
        client=client,
        code=code,
        mode=Lot.Mode.ANONYMOUS,
        head_count=head_count,
        total_weight=Decimal(total_weight),
    )
    intake = Intake.objects.create(
        client=client,
        date=date,
        mode=Intake.Mode.LOT,
        head_count=head_count,
        total_weight=Decimal(total_weight),
        lot=lot,
    )
    return intake, lot
