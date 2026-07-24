"""Phase 5: advisors. The value is auditability — the snapshot IS the record."""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.advisors.models import Advisor, AdvisorReport
from apps.advisors.services import generate_report
from apps.advisors.snapshot import build_snapshot
from apps.clients.models import Client
from apps.feed.models import FeedingEvent, FeedType
from apps.feed.services import register_feeding
from apps.livestock.models import Animal
from apps.livestock.services import register_weighing

pytestmark = pytest.mark.django_db


def _client(name="La Esperanza"):
    return Client.objects.create(name=name, kind=Client.Kind.BOARDING)


def _advisor(slug="livestock"):
    return Advisor.objects.get(slug=slug)  # seeded by migration


def _animal(client, tag="A-001", weight="320"):
    return Animal.objects.create(
        client=client, ear_tag=tag, category="steer", entry_date="2026-01-10",
        entry_weight=Decimal(weight), current_weight=Decimal(weight),
    )


# --- seed --------------------------------------------------------------------

def test_three_advisors_are_seeded():
    assert set(Advisor.objects.values_list("slug", flat=True)) == {"livestock", "finance", "admin"}


def test_advisors_have_prompts():
    assert all(a.system_prompt for a in Advisor.objects.all())


# --- snapshot ----------------------------------------------------------------

def test_snapshot_is_scoped_to_one_client():
    a, b = _client("A"), _client("B")
    _animal(a, "A-1")
    _animal(b, "B-1")
    snap = build_snapshot(client=a)
    assert snap["client"]["id"] == a.id
    assert snap["herd"]["head_count"] == 1  # only A's animal


def test_snapshot_is_json_safe():
    import json
    client = _client()
    _animal(client)
    snap = build_snapshot(client=client)
    json.dumps(snap)  # must not raise (Decimals/dates stringified)


def test_snapshot_carries_the_dashboard_metrics():
    client = _client()
    animal = _animal(client)
    register_weighing(animal=animal, weight="320", date="2026-02-01")
    register_weighing(animal=animal, weight="380", date="2026-03-03")
    register_feeding(
        client=client, feed_type=FeedType.objects.create(name="Maíz"), quantity="420",
        unit_price="285", origin=FeedingEvent.Origin.OWN_STOCK, date="2026-02-15", animal=animal,
    )
    snap = build_snapshot(client=client)
    assert snap["conversion"]["conversion"] == "7"  # 420 fed / 60 gained, stringified
    assert "cost" in snap and "mortality" in snap


# --- generation --------------------------------------------------------------

@override_settings(DEBUG=True)
def test_generate_report_persists_snapshot_and_output():
    client = _client()
    _animal(client)
    report = generate_report(advisor=_advisor(), client=client)
    assert AdvisorReport.objects.count() == 1
    assert report.input_snapshot["client"]["id"] == client.id
    assert report.output  # mock client produced text
    assert report.model_id == "mock-advisor-double"


@override_settings(DEBUG=True)
def test_report_output_references_real_data():
    client = _client()
    _animal(client, weight="333")
    report = generate_report(advisor=_advisor(), client=client)
    # Mock echoes head_count into the text — proves it saw the snapshot.
    assert "Cabezas: 1" in report.output


@override_settings(DEBUG=True)
def test_inactive_advisor_is_rejected():
    client = _client()
    advisor = _advisor()
    advisor.is_active = False
    advisor.save()
    with pytest.raises(ValidationError):
        generate_report(advisor=advisor, client=client)


@override_settings(DEBUG=True)
def test_report_is_read_only_no_reinference_on_read():
    client = _client()
    _animal(client)
    report = generate_report(advisor=_advisor(), client=client)
    # Reading the stored report does not create a second one.
    fetched = AdvisorReport.objects.get(pk=report.pk)
    assert fetched.output == report.output
    assert AdvisorReport.objects.count() == 1


@override_settings(DEBUG=True)
def test_each_generation_is_a_new_report():
    client = _client()
    _animal(client)
    advisor = _advisor()
    generate_report(advisor=advisor, client=client)
    generate_report(advisor=advisor, client=client)
    assert AdvisorReport.objects.filter(client=client).count() == 2


# --- endpoints ---------------------------------------------------------------

def test_routes_resolve():
    from django.urls import reverse
    assert reverse("advisor-list") == "/api/advisors/"
    assert reverse("advisor-report-list") == "/api/advisor-reports/"
