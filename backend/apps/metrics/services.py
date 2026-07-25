"""LIVE-DOC:START — astro-drf-aws live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

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


# --- pen cost summary (Phase 7) ----------------------------------------------

def pen_cost_summary(*, client, start=None, end=None):
    """Cost-side pen closeout (adr-33 decision 7): kilos served and feed cost per
    pen over the period, read from `FeedingEvent.pen`.

    Only the cost side — the gain side (kg produced, conversion per pen) needs
    animal/lot → pen placement and is deferred to Phase 7b. Feed cost counts own
    stock only, matching billing (adr-25 rule 4): client-stock feed is served but
    not charged, so its cost is `0` while its kilos still count.
    """
    lo, hi = _bounds(start, end)
    rows = (
        FeedingEvent.objects.filter(
            client=client, pen__isnull=False, date__gte=lo, date__lte=hi
        )
        .values("pen", "pen__code")
        .annotate(kilos_fed=Sum("quantity"))
        .order_by("pen__code")
    )

    pens = []
    for row in rows:
        events = FeedingEvent.objects.filter(
            client=client, pen_id=row["pen"], date__gte=lo, date__lte=hi,
            origin=FeedingEvent.Origin.OWN_STOCK,
        )
        feed_cost = sum((e.total_cost for e in events), ZERO)
        pens.append(
            {
                "pen": row["pen"],
                "code": row["pen__code"],
                "kilos_fed": row["kilos_fed"] or ZERO,
                "feed_cost": feed_cost,
            }
        )
    return pens


# --- pen occupancy (Phase 7b) ------------------------------------------------

def pen_occupancy_report(*, pen, start=None, end=None):
    """Pen-level monitoring (adr-34 decision 5): current occupancy, head moved in
    the period, and kilos fed to the pen.

    This is the honest half of the pen closeout — occupancy is derivable from the
    placement events (adr-34 decision 1). Per-pen feed conversion stays deferred:
    it needs attributing weighings to a pen stay, which a placed-head count does
    not give (adr-29 rule 2 — no fabricated number)."""
    from apps.feedyard.models import PenPlacement
    from apps.feedyard.services import pen_occupancy

    lo, hi = _bounds(start, end)

    moved_in = moved_out = 0
    for placement in PenPlacement.objects.filter(pen=pen, date__gte=lo, date__lte=hi):
        head = placement.head or 0
        if placement.direction == PenPlacement.Direction.IN:
            moved_in += head
        else:
            moved_out += head

    kilos_fed_to_pen = (
        FeedingEvent.objects.filter(pen=pen, date__gte=lo, date__lte=hi).aggregate(
            t=Sum("quantity")
        )["t"]
        or ZERO
    )

    return {
        "pen": pen.id,
        "code": pen.code,
        "current_head": pen_occupancy(pen=pen, as_of=(end or None)),
        "head_moved_in": moved_in,
        "head_moved_out": moved_out,
        "kilos_fed": kilos_fed_to_pen,
    }


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


# --- inventory & weather (Phase 10) ------------------------------------------


def input_stock_report(*, owner_kind=None, client=None):
    """Current derived stock per active input type (adr-37 decision 1).

    Reads `inventory` movements; stock is Σin − Σout, never a stored field. When
    `owner_kind`/`client` are given the report is scoped to that owner.
    """
    from apps.inventory.models import InputStockMovement, InputType, OwnerKind
    from apps.inventory.services import current_stock

    owner_kind = owner_kind or OwnerKind.OWN
    rows = []
    for input_type in InputType.objects.filter(is_active=True):
        rows.append({
            "input_type": input_type.id,
            "name": input_type.name,
            "unit": input_type.unit,
            "stock": current_stock(
                input_type=input_type, owner_kind=owner_kind, client=client
            ),
        })
    return {"owner_kind": owner_kind, "client": client.id if client else None, "rows": rows}


def rainfall_summary(*, start=None, end=None, site=None):
    """Rainfall over the period: total mm, rainy days, days logged (adr-37 decision 5)."""
    from apps.weather.models import WeatherLog

    lo, hi = _bounds(start, end)
    logs = WeatherLog.objects.filter(date__gte=lo, date__lte=hi)
    if site is not None:
        logs = logs.filter(site=site)

    total = logs.aggregate(t=Sum("rainfall_mm"))["t"] or ZERO
    rainy = logs.filter(rainfall_mm__gt=ZERO).count()
    return {
        "period": {"start": start, "end": end},
        "site": site,
        "total_mm": total,
        "rainy_days": rainy,
        "days_logged": logs.count(),
    }


# --- traceability (Phase 11) -------------------------------------------------


def caravana_coverage(*, client):
    """Share of a client's ACTIVE head that carry an official caravana (adr-38 decision 5).

    Returns `ratio=None` with a `not_calculable` reason when the client has no active
    head — never a filled 0 (adr-29 rule 2). Coverage is counted over individual animals
    only; anonymous lots have no per-head identity to caravana.
    """
    from apps.livestock.models import Animal
    from apps.traceability.models import Caravana

    active = Animal.objects.filter(client=client, status=Animal.Status.ACTIVE)
    total = active.count()
    if total == 0:
        return {
            "client": client.id,
            "active_head": 0,
            "caravanned": 0,
            "ratio": None,
            "not_calculable": "no_active_head",
        }

    caravanned = (
        Caravana.objects.filter(animal__in=active)
        .values("animal_id")
        .distinct()
        .count()
    )
    return {
        "client": client.id,
        "active_head": total,
        "caravanned": caravanned,
        "ratio": Decimal(caravanned) / Decimal(total),
        "not_calculable": None,
    }


# --- gross margin & reference FX (Phase 12) ----------------------------------


def gross_margin(
    *, client, start=None, end=None, price_source, category,
    price_avg_field="price_avg", currency=None, fx_source=None,
):
    """Reference gross margin: income (kg produced × market price) − period cost (adr-39).

    Income is a REFERENCE value (kilos_gained × the latest market price for `category`
    from `price_source`), not money collected — it posts no ledger entry (decision 5).
    Cost is `cost_breakdown` total (debits only, adr-29 rule 4). Returns `null` with a
    reason when any input is missing (decision 4); when `currency` is given the ARS margin
    always comes back and only its conversion is `null` if there is no `FxRate`.
    """
    from apps.fx.services import convert_ars
    from apps.market.services import latest_price

    _, hi = _bounds(start, end)
    growth = kilos_gained(client=client, start=start, end=end)
    gained = growth["kilos_gained"]
    cost = cost_breakdown(client=client, start=start, end=end)["total"]

    base = {
        "client": client.id,
        "period": {"start": start, "end": end},
        "kilos_gained": gained,
        "cost": cost,
        **_seg(growth),
    }

    if growth["segments_measured"] == 0:
        return {**base, "reference_price": None, "income": None, "margin": None,
                "currency": None, "margin_currency": None, "not_calculable": "no_measured_growth"}
    if gained <= ZERO:
        return {**base, "reference_price": None, "income": None, "margin": None,
                "currency": None, "margin_currency": None, "not_calculable": "no_weight_gain"}

    price = latest_price(source_slug=price_source, category=category, on_or_before=hi)
    price_value = getattr(price, price_avg_field, None) if price is not None else None
    if price_value is None:
        return {**base, "reference_price": None, "income": None, "margin": None,
                "currency": None, "margin_currency": None, "not_calculable": "no_reference_price"}

    income = gained * price_value
    margin = income - cost
    result = {**base, "reference_price": price_value, "income": income, "margin": margin,
              "currency": None, "margin_currency": None, "not_calculable": ""}

    if currency is not None:
        converted, row = convert_ars(
            amount_ars=margin, currency=currency, on_or_before=hi, source=fx_source
        )
        result["currency"] = currency
        result["margin_currency"] = converted
        result["fx_rate"] = row.rate if row is not None else None
        if converted is None:
            result["not_calculable"] = "no_fx_rate"

    return result
