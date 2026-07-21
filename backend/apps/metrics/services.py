"""Derived metrics for the client dashboard (Phase 3).

No models: every number here is computed from the operational events. This app
owns *how* the numbers are derived so the frontend never does auditable maths in
the browser, and so the advisors (Phase 5) consume exactly what the dashboard
shows — one definition per metric, not two.

Every function that cannot honestly produce a number returns `None` plus a reason,
never a zero or a guess. A missing metric is readable; a fabricated one is not.
"""

from datetime import date as date_cls
from decimal import Decimal

from django.db.models import Sum

from apps.feed.models import FeedingEvent
from apps.ledger.models import Concept, Direction, LedgerEntry
from apps.livestock.models import Animal, Death, Exit, Intake, Lot
from apps.livestock.services import growth_series

ZERO = Decimal("0")


def _bounds(start, end):
    """Normalise the period; either end may be open."""
    return (start or date_cls.min, end or date_cls.max)


# --- herd --------------------------------------------------------------------

def herd_snapshot(*, client):
    """Live head and kilos right now, across individual animals and lots."""
    animals = Animal.objects.filter(client=client, status=Animal.Status.ACTIVE)
    lots = Lot.objects.filter(client=client, status=Lot.Status.ACTIVE)

    animal_head = animals.count()
    animal_kg = animals.aggregate(t=Sum("current_weight"))["t"] or ZERO
    lot_head = lots.aggregate(t=Sum("head_count"))["t"] or 0
    lot_kg = lots.aggregate(t=Sum("total_weight"))["t"] or ZERO

    head = animal_head + lot_head
    kg = animal_kg + lot_kg
    return {
        "head_count": head,
        "total_weight": kg,
        "average_weight": (kg / Decimal(head)) if head else None,
        "animals": animal_head,
        "lots": lots.count(),
    }


# --- growth ------------------------------------------------------------------

def kilos_gained(*, client, start=None, end=None):
    """Kilos put on during the period, summed over every target of the client.

    Only segments whose ADG is calculable contribute (adr-28 rule 2): a lot whose
    head count moved between two readings is skipped rather than guessed. The
    result carries how many segments were skipped so the caller can tell "no
    growth" apart from "not measured".
    """
    lo, hi = _bounds(start, end)
    total = ZERO
    measured = skipped = 0

    for animal in Animal.objects.filter(client=client):
        series = [s for s in growth_series(animal=animal) if lo <= s["date"] <= hi]
        gained, m, s_ = _sum_segments(series, head_factor=lambda row: 1)
        total += gained
        measured += m
        skipped += s_

    for lot in Lot.objects.filter(client=client):
        series = [s for s in growth_series(lot=lot) if lo <= s["date"] <= hi]
        gained, m, s_ = _sum_segments(series, head_factor=lambda row: row["head_count"] or 0)
        total += gained
        measured += m
        skipped += s_

    return {
        "kilos_gained": total,
        "segments_measured": measured,
        "segments_skipped": skipped,
    }


def _sum_segments(series, *, head_factor):
    """Sum per-head deltas × head count over the calculable segments only."""
    total = ZERO
    measured = skipped = 0
    previous = None
    for row in series:
        if previous is not None:
            if row["adg"] is None:
                skipped += 1
            else:
                delta = row["weight_per_head"] - previous["weight_per_head"]
                total += delta * Decimal(head_factor(row))
                measured += 1
        previous = row
    return total, measured, skipped


def kilos_fed(*, client, start=None, end=None):
    lo, hi = _bounds(start, end)
    return (
        FeedingEvent.objects.filter(client=client, date__gte=lo, date__lte=hi).aggregate(
            t=Sum("quantity")
        )["t"]
        or ZERO
    )


def conversion(*, client, start=None, end=None):
    """Feed conversion: kg of feed per kg gained. The metric that justifies the system.

    Returns `None` when there is nothing honest to divide by — no growth measured,
    or growth that came out flat or negative.
    """
    fed = kilos_fed(client=client, start=start, end=end)
    growth = kilos_gained(client=client, start=start, end=end)
    gained = growth["kilos_gained"]

    if growth["segments_measured"] == 0:
        return {"conversion": None, "not_calculable": "no_measured_growth",
                "kilos_fed": fed, "kilos_gained": gained, **_seg(growth)}
    if gained <= ZERO:
        return {"conversion": None, "not_calculable": "no_weight_gain",
                "kilos_fed": fed, "kilos_gained": gained, **_seg(growth)}

    return {"conversion": fed / gained, "not_calculable": "",
            "kilos_fed": fed, "kilos_gained": gained, **_seg(growth)}


def _seg(growth):
    return {
        "segments_measured": growth["segments_measured"],
        "segments_skipped": growth["segments_skipped"],
    }


# --- mortality ---------------------------------------------------------------

def mortality(*, client, start=None, end=None):
    """Dead head over head that entered. Rate is `None` when nothing entered."""
    lo, hi = _bounds(start, end)

    dead = 0
    for death in Death.objects.filter(date__gte=lo, date__lte=hi).select_related("animal", "lot"):
        target = death.animal or death.lot
        if target and target.client_id == client.id:
            dead += death.head_count or 1

    entered = (
        Intake.objects.filter(client=client, date__gte=lo, date__lte=hi).aggregate(
            t=Sum("head_count")
        )["t"]
        or 0
    )

    return {
        "dead_head": dead,
        "entered_head": entered,
        "rate": (Decimal(dead) / Decimal(entered)) if entered else None,
        "not_calculable": "" if entered else "no_intake_in_period",
    }


# --- cost and account --------------------------------------------------------

def cost_breakdown(*, client, start=None, end=None):
    """Debits of the period grouped by concept. Credits are not costs."""
    lo, hi = _bounds(start, end)
    rows = (
        LedgerEntry.objects.filter(
            account=client.account, direction=Direction.DEBIT, date__gte=lo, date__lte=hi
        )
        .values("concept")
        .annotate(total=Sum("amount"))
    )
    by_concept = {row["concept"]: row["total"] or ZERO for row in rows}
    return {
        "by_concept": {c.value: by_concept.get(c.value, ZERO) for c in Concept if c != Concept.PAYMENT},
        "total": sum(by_concept.values(), ZERO),
    }


def daily_cost(*, client, start=None, end=None):
    """One row per day that had charges, broken down by concept."""
    lo, hi = _bounds(start, end)
    rows = (
        LedgerEntry.objects.filter(
            account=client.account, direction=Direction.DEBIT, date__gte=lo, date__lte=hi
        )
        .values("date", "concept")
        .annotate(total=Sum("amount"))
        .order_by("date")
    )

    days = {}
    for row in rows:
        day = days.setdefault(row["date"], {"date": row["date"], "total": ZERO, "by_concept": {}})
        day["by_concept"][row["concept"]] = row["total"]
        day["total"] += row["total"]
    return list(days.values())


def account_evolution(*, client, start=None, end=None):
    """Running balance, one point per movement. Positive means the client owes."""
    lo, hi = _bounds(start, end)

    opening = ZERO
    for entry in LedgerEntry.objects.filter(account=client.account, date__lt=lo):
        opening += entry.amount if entry.direction == Direction.DEBIT else -entry.amount

    running = opening
    points = []
    for entry in LedgerEntry.objects.filter(
        account=client.account, date__gte=lo, date__lte=hi
    ).order_by("date", "id"):
        running += entry.amount if entry.direction == Direction.DEBIT else -entry.amount
        points.append(
            {
                "entry": entry.id,
                "date": entry.date,
                "direction": entry.direction,
                "concept": entry.concept,
                "amount": entry.amount,
                "balance": running,
            }
        )

    return {"opening_balance": opening, "closing_balance": running, "points": points}


# --- consistency -------------------------------------------------------------

def inconsistencies(*, client):
    """Data problems worth surfacing on the dashboard rather than hiding.

    Today: rations dated after the animal died. The system accepts them (late data
    entry is legitimate) but somebody should look.
    """
    findings = []
    dead = Animal.objects.filter(client=client, status=Animal.Status.DEAD)
    for animal in dead:
        death = Death.objects.filter(animal=animal).order_by("date").first()
        if not death:
            continue
        late = FeedingEvent.objects.filter(animal=animal, date__gt=death.date)
        if late.exists():
            findings.append(
                {
                    "kind": "feeding_after_death",
                    "animal": animal.id,
                    "ear_tag": animal.ear_tag,
                    "death_date": death.date,
                    "events": list(late.values_list("id", flat=True)),
                }
            )
    return findings


# --- summary -----------------------------------------------------------------

def summary(*, client, start=None, end=None):
    """Everything the dashboard header needs, in one call."""
    client.account.refresh_from_db()
    return {
        "client": client.id,
        "period": {"start": start, "end": end},
        "herd": herd_snapshot(client=client),
        "balance": client.account.balance_cached,
        "cost": cost_breakdown(client=client, start=start, end=end),
        "conversion": conversion(client=client, start=start, end=end),
        "mortality": mortality(client=client, start=start, end=end),
        "inconsistencies": inconsistencies(client=client),
    }
