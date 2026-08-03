"""LIVE-DOC:START — alvs-feedlot-campo live-doc; see [[adr-17-live-doc-backlinks]]
Docs: [[BACKEND]]
LIVE-DOC:END"""

"""FX services — the only sanctioned write path for a reference rate.

`register_fx_rate` upserts idempotently by `(currency, date, source)` and rejects a
non-positive rate (adr-39 decision 2). `latest_rate` returns the last known value at or
before a date, tolerant to gaps like `market.latest_price`. `convert_ars` expresses an
ARS amount in another currency, returning `None` when there is no rate to divide by.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.fx.models import FxRate

ZERO = Decimal("0")


@transaction.atomic
def register_fx_rate(*, currency, date, rate, source="manual"):
    """Upsert a reference rate. Posts no ledger entry — it redenominates nothing."""
    if rate is None or Decimal(rate) <= ZERO:
        raise ValidationError("FX rate must be positive.")

    obj, _ = FxRate.objects.update_or_create(
        currency=currency, date=date, source=source, defaults={"rate": rate}
    )
    return obj


def latest_rate(*, currency, on_or_before=None, source=None):
    """Most recent rate for a currency, at or before a date. `None` when unknown."""
    qs = FxRate.objects.filter(currency=currency)
    if source is not None:
        qs = qs.filter(source=source)
    if on_or_before is not None:
        qs = qs.filter(date__lte=on_or_before)
    return qs.order_by("-date").first()


def convert_ars(*, amount_ars, currency, on_or_before=None, source=None):
    """Express an ARS amount in `currency`. Returns `(converted, rate_row)` or `(None, None)`."""
    row = latest_rate(currency=currency, on_or_before=on_or_before, source=source)
    if row is None:
        return None, None
    return Decimal(amount_ars) / row.rate, row
