"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
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

from apps.breeding.models import (
    Calving,
    CalvingOutcome,
    PregnancyCheck,
    PregnancyResult,
    Service,
    Weaning,
)
from apps.feed.models import FeedingEvent
from apps.genetics.models import Direction as MoveDir, SemenBatch, SemenMovement
from apps.genetics.services import current_semen_stock
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


def target_kilos_gained(*, animal=None, lot=None):
    """Kilos put on by ONE animal or lot over its whole series, honest-cut.

    Reuses the same segment logic as `kilos_gained` so there is a single
    definition of "kilos gained" (adr-29 rule 1): only segments whose ADG is
    calculable count (adr-28 rule 2). Used by the sale settlement (adr-43) to
    value a boarding client's engorde commission. Returns kilos plus the
    measured/skipped segment counts so the caller can tell "no growth" apart
    from "not measured".
    """
    if animal is not None:
        series = growth_series(animal=animal)
        gained, measured, skipped = _sum_segments(series, head_factor=lambda row: 1)
    else:
        series = growth_series(lot=lot)
        gained, measured, skipped = _sum_segments(
            series, head_factor=lambda row: row["head_count"] or 0
        )
    return {
        "kilos_gained": gained,
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


# --- pen conversion, the honest cut (Phase 4b) -------------------------------

def pen_conversion(*, pen, start=None, end=None):
    """Per-pen feed conversion — the honest cut of the closeout that adr-33 decision
    7 and adr-34 decision 5 deferred (adr-42).

    Conversion is kg fed to the pen ÷ kg gained IN the pen. Kilos fed read from
    `FeedingEvent.pen`. Kilos gained are attributed to the pen ONLY for weighing
    segments a target spent entirely inside one continuous stay in THIS pen, derived
    from `PenPlacement` in/out events (adr-42 decision 2). A segment whose interval
    spans a pen change — or a target with no placement pinning it here — is NOT
    attributed: guessing which pen grew the animal is exactly the fabricated number
    adr-29 rule 2 forbids. Segments that can't be pinned are counted so "grew
    elsewhere / not placed" reads apart from "did not grow" (decision 3).

    Returns `conversion=None` with a `not_calculable` reason whenever there is
    nothing honest to divide (decision 4)."""
    from apps.feedyard.models import PenPlacement

    # Views hand dates in already parsed; coerce ISO strings too so the Python-level
    # segment comparisons below never mix str and date.
    start = date_cls.fromisoformat(start) if isinstance(start, str) else start
    end = date_cls.fromisoformat(end) if isinstance(end, str) else end
    lo, hi = _bounds(start, end)

    fed = (
        FeedingEvent.objects.filter(pen=pen, date__gte=lo, date__lte=hi).aggregate(
            t=Sum("quantity")
        )["t"]
        or ZERO
    )

    gained = ZERO
    attributed = unattributed = skipped = 0

    # Only targets ever placed into this pen can contribute gain here.
    animal_ids = set(
        PenPlacement.objects.filter(pen=pen, animal__isnull=False).values_list(
            "animal_id", flat=True
        )
    )
    lot_ids = set(
        PenPlacement.objects.filter(pen=pen, lot__isnull=False).values_list(
            "lot_id", flat=True
        )
    )

    for animal in Animal.objects.filter(id__in=animal_ids):
        events = list(PenPlacement.objects.filter(animal=animal).order_by("date", "id"))
        series = [s for s in growth_series(animal=animal) if lo <= s["date"] <= hi]
        g, a, u, s_ = _attribute_segments(
            series, events, pen_id=pen.id, head_factor=lambda row: 1
        )
        gained += g
        attributed += a
        unattributed += u
        skipped += s_

    for lot in Lot.objects.filter(id__in=lot_ids):
        events = list(PenPlacement.objects.filter(lot=lot).order_by("date", "id"))
        series = [s for s in growth_series(lot=lot) if lo <= s["date"] <= hi]
        g, a, u, s_ = _attribute_segments(
            series, events, pen_id=pen.id, head_factor=lambda row: row["head_count"] or 0
        )
        gained += g
        attributed += a
        unattributed += u
        skipped += s_

    base = {
        "pen": pen.id,
        "code": pen.code,
        "kilos_fed": fed,
        "kilos_gained": gained,
        "segments_attributed": attributed,
        "segments_unattributed": unattributed,
        "segments_skipped": skipped,
    }
    if attributed == 0:
        return {**base, "conversion": None, "not_calculable": "no_attributable_growth"}
    if gained <= ZERO:
        return {**base, "conversion": None, "not_calculable": "no_weight_gain"}
    if fed <= ZERO:
        return {**base, "conversion": None, "not_calculable": "no_feed_recorded"}
    return {**base, "conversion": fed / gained, "not_calculable": ""}


def _attribute_segments(series, events, *, pen_id, head_factor):
    """Sum gain over calculable segments spent wholly in one stay in `pen_id` (adr-42
    decisions 2, 3).

    A segment (previous→row) is attributed to the pen the target sat in as of the
    previous reading, but only when no placement event falls strictly inside the
    interval (no pen change mid-segment). Non-calculable ADG segments (adr-28 rule 2)
    are skipped; calculable segments belonging to another pen — or to no pen — are
    counted as unattributed. Returns (gained, attributed, unattributed, skipped)."""
    total = ZERO
    attributed = unattributed = skipped = 0
    previous = None
    for row in series:
        if previous is not None:
            if row["adg"] is None:
                skipped += 1
            else:
                a, b = previous["date"], row["date"]
                moved_mid = any(a < e.date < b for e in events)
                where = _pen_at(events, a)
                if not moved_mid and where == pen_id:
                    delta = row["weight_per_head"] - previous["weight_per_head"]
                    total += delta * Decimal(head_factor(row))
                    attributed += 1
                else:
                    unattributed += 1
        previous = row
    return total, attributed, unattributed, skipped


def _pen_at(events, d):
    """Pen id the target sits in as of date `d` inclusive, or None (adr-42 decision 2).

    `events` is the target's `PenPlacement` rows ordered by (date, id); an `in` sets
    the pen, an `out` clears it."""
    from apps.feedyard.models import PenPlacement

    current = None
    for event in events:
        if event.date > d:
            break
        current = event.pen_id if event.direction == PenPlacement.Direction.IN else None
    return current


def pen_closeout(*, pen, start=None, end=None):
    """The full honest pen closeout: occupancy (adr-34) plus feed conversion (adr-42).

    Both halves derive from events; the conversion carries its own `not_calculable`
    when no segment can be honestly pinned to the pen. The occupancy half is always
    affirmable; the conversion half is the honest subset."""
    occupancy = pen_occupancy_report(pen=pen, start=start, end=end)
    return {**occupancy, "conversion": pen_conversion(pen=pen, start=start, end=end)}


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


# --- reproduction (adr-46 decision 8) ----------------------------------------
#
# Pure functions over the breeding events of one client. Every rate is a ratio of
# two honest event counts; when the denominator is zero the rate is `None` plus a
# reason, never a fabricated zero (adr-29 rule 2). A "% pregnancy = 0" and a "no
# services to evaluate" are opposite situations and must stay distinguishable.

def _dam_key(event):
    """The reproductive unit an event targets — an animal or a lot."""
    return ("animal", event.animal_id) if event.animal_id else ("lot", event.lot_id)


def pregnancy_rate(*, client, start=None, end=None):
    """Pregnant diagnoses over services in the period. `None` if nothing served."""
    lo, hi = _bounds(start, end)
    serviced = Service.objects.filter(
        client=client, date__gte=lo, date__lte=hi
    ).count()
    pregnant = PregnancyCheck.objects.filter(
        client=client, result=PregnancyResult.PREGNANT, date__gte=lo, date__lte=hi
    ).count()
    return {
        "serviced": serviced,
        "pregnant": pregnant,
        "rate": (Decimal(pregnant) / Decimal(serviced)) if serviced else None,
        "not_calculable": "" if serviced else "no_services_in_period",
    }


def calving_rate(*, client, start=None, end=None):
    """Calvings over pregnant diagnoses. `None` if nothing was diagnosed pregnant."""
    lo, hi = _bounds(start, end)
    pregnant = PregnancyCheck.objects.filter(
        client=client, result=PregnancyResult.PREGNANT, date__gte=lo, date__lte=hi
    ).count()
    calvings = Calving.objects.filter(
        client=client, date__gte=lo, date__lte=hi
    ).count()
    return {
        "pregnant": pregnant,
        "calvings": calvings,
        "rate": (Decimal(calvings) / Decimal(pregnant)) if pregnant else None,
        "not_calculable": "" if pregnant else "no_pregnancy_checks",
    }


def weaning_rate(*, client, start=None, end=None):
    """Weanings over calvings. `None` if nothing calved."""
    lo, hi = _bounds(start, end)
    calvings = Calving.objects.filter(
        client=client, date__gte=lo, date__lte=hi
    ).count()
    weanings = Weaning.objects.filter(
        client=client, date__gte=lo, date__lte=hi
    ).count()
    return {
        "calvings": calvings,
        "weanings": weanings,
        "rate": (Decimal(weanings) / Decimal(calvings)) if calvings else None,
        "not_calculable": "" if calvings else "no_calvings",
    }


def calving_interval(*, client, start=None, end=None):
    """Average days between successive calvings per dam (IEP). Needs at least one
    dam with two calvings; otherwise `None` with the reason. The interval is a
    historical span, so it reads every calving up to the period end, not only the
    window — bounding it to the window would hide the previous calving that closes
    the interval."""
    _, hi = _bounds(start, end)
    calvings = (
        Calving.objects.filter(client=client, date__lte=hi)
        .order_by("date", "id")
    )
    by_dam = {}
    for calving in calvings:
        by_dam.setdefault(_dam_key(calving), []).append(calving.date)

    intervals = []
    for dates in by_dam.values():
        for prev, nxt in zip(dates, dates[1:]):
            intervals.append((nxt - prev).days)

    if not intervals:
        return {
            "dams_with_interval": 0,
            "average_days": None,
            "not_calculable": "insufficient_calving_history",
        }
    return {
        "dams_with_interval": len(by_dam),
        "average_days": Decimal(sum(intervals)) / Decimal(len(intervals)),
        "not_calculable": "",
    }


def kg_weaned_per_dam(*, client, start=None, end=None):
    """Total weaning weight over the number of dams weaned in the period. `None`
    if nothing was weaned."""
    lo, hi = _bounds(start, end)
    weanings = Weaning.objects.filter(client=client, date__gte=lo, date__lte=hi)
    dams = set()
    total = ZERO
    for weaning in weanings:
        dams.add(_dam_key(weaning))
        total += weaning.weaning_weight or ZERO
    return {
        "dams": len(dams),
        "total_kg": total,
        "kg_per_dam": (total / Decimal(len(dams))) if dams else None,
        "not_calculable": "" if dams else "no_weanings",
    }


def reproduction(*, client, start=None, end=None):
    """The five derived reproductive metrics for one client and period, each
    carrying its own `not_calculable` (adr-46 decision 8)."""
    return {
        "pregnancy_rate": pregnancy_rate(client=client, start=start, end=end),
        "calving_rate": calving_rate(client=client, start=start, end=end),
        "weaning_rate": weaning_rate(client=client, start=start, end=end),
        "calving_interval": calving_interval(client=client, start=start, end=end),
        "kg_weaned_per_dam": kg_weaned_per_dam(client=client, start=start, end=end),
    }


# --- genetics: semen stock (adr-47 decision 8) -------------------------------
#
# Derived straws per batch and per sire = Σin − Σout, total available, and per-sire
# usage over the period. Not client-scoped: genetics is the feedyard's own asset.
# `None` plus a reason when there are no movements at all — "0 straws" and "this
# sire's semen was never loaded" are opposite situations (adr-29 rule 2).

def semen_stock_report(*, sire=None, semen_batch=None, start=None, end=None):
    lo, hi = _bounds(start, end)

    batches = SemenBatch.objects.select_related("sire")
    if semen_batch is not None:
        batches = batches.filter(pk=semen_batch)
    if sire is not None:
        batches = batches.filter(sire_id=sire)

    per_batch = []
    per_sire = {}
    total_available = ZERO
    for batch in batches:
        stock = current_semen_stock(semen_batch=batch)
        total_available += stock
        per_batch.append({
            "semen_batch": batch.id,
            "batch_code": batch.batch_code,
            "sire": batch.sire_id,
            "sire_name": batch.sire.name,
            "straws": stock,
        })
        row = per_sire.setdefault(
            batch.sire_id, {"sire": batch.sire_id, "sire_name": batch.sire.name,
                            "straws": ZERO, "used": ZERO}
        )
        row["straws"] += stock

    usage = (
        SemenMovement.objects.filter(direction=MoveDir.OUT, date__gte=lo, date__lte=hi)
        .filter(**({"semen_batch_id": semen_batch} if semen_batch is not None else {}))
        .filter(**({"semen_batch__sire_id": sire} if sire is not None else {}))
        .values("semen_batch__sire_id")
        .annotate(used=Sum("straws"))
    )
    for row in usage:
        sire_id = row["semen_batch__sire_id"]
        target = per_sire.setdefault(
            sire_id, {"sire": sire_id, "sire_name": None, "straws": ZERO, "used": ZERO}
        )
        target["used"] = row["used"] or ZERO

    if not per_batch and not per_sire:
        return {
            "per_batch": [],
            "per_sire": [],
            "total_available": None,
            "not_calculable": "no_semen_movements",
        }
    return {
        "per_batch": per_batch,
        "per_sire": list(per_sire.values()),
        "total_available": total_available,
        "not_calculable": "",
    }
