"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""Breeding (adr-46): the reproductive cycle service → tacto → parición → destete.

Only an AI/IATF Service on a boarding client posts a ledger entry — a `service`
debit for the insemination fee (decision 6). Natural/own services, embryo
transfers, pregnancy checks, calvings and weanings post NONE (decision 1). A
service decrements a genetics SemenMovement/EmbryoMovement `out` (decision 7); a
live individual calving creates the calf Animal (decision 4). Reproductive status
and genealogy are DERIVED, never stored (decision 3).
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.clients.models import Client
from apps.genetics.models import (
    Direction as MoveDir,
    EmbryoBatch,
    EmbryoMovement,
    SemenBatch,
    SemenMovement,
    Sire,
)
from apps.genetics.services import register_embryo_flush, register_semen_movement
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Animal, Category, Lot
from apps.breeding.models import (
    Calving,
    IatfProtocol,
    Method,
    PregnancyResult,
    Service,
    Weaning,
    WeaningPurpose,
)
from apps.breeding.services import (
    register_calving,
    register_pregnancy_check,
    register_service,
    register_weaning,
)

pytestmark = pytest.mark.django_db


def _cow(client, ear_tag="V-001"):
    return Animal.objects.create(
        client=client, ear_tag=ear_tag, category=Category.COW, sex="female",
        entry_date="2026-01-10",
    )


def _stocked_batch(sire, straws="20"):
    batch = SemenBatch.objects.create(sire=sire, batch_code="B-001")
    register_semen_movement(
        semen_batch=batch, direction=MoveDir.IN, straws=straws,
        reason="purchase", date="2026-02-01",
    )
    return batch


def test_ai_service_on_boarding_client_posts_service_debit_and_decrements_semen():
    boarding = Client.objects.create(name="Cliente Hotel", kind=Client.Kind.BOARDING)
    sire = Sire.objects.create(name="Toro A", breed="Angus")
    batch = _stocked_batch(sire)
    cow = _cow(boarding)

    service = register_service(
        animal=cow, date="2026-03-01", method=Method.AI, sire=sire,
        semen_batch=batch, service_price="1500",
    )

    entry = LedgerEntry.objects.get(source_kind="breeding_service")
    assert entry.account == boarding.account
    assert entry.direction == Direction.DEBIT
    assert entry.concept == Concept.SERVICE
    assert entry.amount == Decimal("1500.00")
    assert entry.source_id == service.id
    boarding.account.refresh_from_db()
    assert boarding.account.balance_cached == Decimal("1500.00")

    out = SemenMovement.objects.get(direction=MoveDir.OUT)
    assert out.semen_batch == batch
    assert out.straws == Decimal("1")


def test_natural_service_posts_no_ledger_entry():
    boarding = Client.objects.create(name="Cliente Hotel", kind=Client.Kind.BOARDING)
    sire = Sire.objects.create(name="Toro Nat")
    cow = _cow(boarding)
    register_service(animal=cow, date="2026-03-01", method=Method.NATURAL, sire=sire)
    assert LedgerEntry.objects.count() == 0
    assert SemenMovement.objects.count() == 0


def test_ai_service_on_own_cattle_decrements_semen_but_posts_no_ledger():
    own = Client.objects.create(name="Propio", kind=Client.Kind.OWN)
    sire = Sire.objects.create(name="Toro Prop")
    batch = _stocked_batch(sire)
    cow = _cow(own)
    register_service(
        animal=cow, date="2026-03-01", method=Method.AI, sire=sire,
        semen_batch=batch, service_price="1500",
    )
    assert LedgerEntry.objects.count() == 0
    assert SemenMovement.objects.filter(direction=MoveDir.OUT).count() == 1


def test_embryo_transfer_decrements_embryo_out_and_posts_no_ledger():
    own = Client.objects.create(name="Propio", kind=Client.Kind.OWN)
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    sire = Sire.objects.create(name="Toro E")
    donor = _cow(own, ear_tag="D-001")
    flush = register_embryo_flush(
        donor=donor, sire=sire, date="2026-02-15", embryos_collected="4",
    )
    batch = EmbryoBatch.objects.get(donor=donor)
    recip = _cow(boarding, ear_tag="R-001")

    register_service(
        animal=recip, date="2026-03-01", method=Method.EMBRYO_TRANSFER,
        embryo_batch=batch, service_price="2000",
    )
    # embryo_transfer is not ai/iatf → no insemination-fee debit even on boarding.
    assert LedgerEntry.objects.count() == 0
    out = EmbryoMovement.objects.get(direction=MoveDir.OUT)
    assert out.embryo_batch == batch
    assert out.quantity == Decimal("1")
    assert flush.id  # flush produced the inventory the transfer consumes


def test_service_rejects_both_and_neither_targets():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    lot = Lot.objects.create(client=boarding, code="L-1", head_count=10)
    cow = _cow(boarding)
    with pytest.raises(ValidationError):
        register_service(date="2026-03-01", method=Method.NATURAL)
    with pytest.raises(ValidationError):
        register_service(animal=cow, lot=lot, date="2026-03-01", method=Method.NATURAL)


def test_service_rejects_inactive_target():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    cow = _cow(boarding)
    cow.status = Animal.Status.DEAD
    cow.save()
    with pytest.raises(ValidationError):
        register_service(animal=cow, date="2026-03-01", method=Method.NATURAL)


def test_ai_service_rejects_insufficient_semen_stock():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    sire = Sire.objects.create(name="Toro A")
    batch = SemenBatch.objects.create(sire=sire, batch_code="EMPTY")  # zero stock
    cow = _cow(boarding)
    with pytest.raises(ValidationError):
        register_service(
            animal=cow, date="2026-03-01", method=Method.AI, sire=sire,
            semen_batch=batch, service_price="1500",
        )
    assert LedgerEntry.objects.count() == 0
    assert Service.objects.count() == 0


def test_iatf_service_rejects_inactive_protocol():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    sire = Sire.objects.create(name="Toro A")
    batch = _stocked_batch(sire)
    cow = _cow(boarding)
    protocol = IatfProtocol.objects.create(name="P1", is_active=False)
    with pytest.raises(ValidationError):
        register_service(
            animal=cow, date="2026-03-01", method=Method.IATF, sire=sire,
            semen_batch=batch, protocol=protocol, service_price="1500",
        )


def test_pregnancy_check_posts_no_ledger_and_derives_calving_date():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    cow = _cow(boarding)
    service = register_service(
        animal=cow, date="2026-03-01", method=Method.NATURAL,
        sire=Sire.objects.create(name="T"),
    )
    check = register_pregnancy_check(
        animal=cow, date="2026-04-15", method="ultrasound",
        result=PregnancyResult.PREGNANT, gestation_days=45, service=service,
    )
    assert LedgerEntry.objects.count() == 0
    assert check.result == PregnancyResult.PREGNANT
    # estimated calving = date + (280 - gestation_days), derived (not stored).
    assert check.estimated_calving_date is not None


def test_live_individual_calving_creates_calf_animal():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    cow = _cow(boarding)
    calving = register_calving(
        animal=cow, date="2026-11-20", outcome="live", calving_ease="normal",
        calf_sex="male", calf_weight="35",
    )
    assert LedgerEntry.objects.count() == 0
    assert calving.calf is not None
    calf = calving.calf
    assert calf.category == Category.CALF
    assert calf.client == boarding
    assert calf.status == Animal.Status.ACTIVE
    assert calf.entry_weight == Decimal("35")
    # genealogy is derived: dam is the calving target, no field added to Animal.
    assert calving.animal == cow


def test_lot_calving_records_births_count_and_no_calf():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    lot = Lot.objects.create(client=boarding, code="L-9", head_count=30)
    calving = register_calving(
        lot=lot, date="2026-11-20", outcome="live", births_count=12,
    )
    assert calving.calf is None
    assert calving.births_count == 12
    assert Calving.objects.count() == 1


def test_stillborn_individual_calving_creates_no_calf():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    cow = _cow(boarding)
    calving = register_calving(animal=cow, date="2026-11-20", outcome="stillborn")
    assert calving.calf is None


def test_weaning_posts_no_ledger_entry():
    boarding = Client.objects.create(name="Hotel", kind=Client.Kind.BOARDING)
    calf = Animal.objects.create(
        client=boarding, ear_tag="C-001", category=Category.CALF,
        entry_date="2026-11-20",
    )
    weaning = register_weaning(
        animal=calf, date="2027-05-20", weaning_weight="180",
        purpose=WeaningPurpose.REPLACEMENT,
    )
    assert LedgerEntry.objects.count() == 0
    assert weaning.weaning_weight == Decimal("180")
    assert weaning.purpose == WeaningPurpose.REPLACEMENT
