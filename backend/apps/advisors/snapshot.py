"""Assemble the input_snapshot an advisor reasons over (adr-27 rule 2).

The advisor never touches the database: this module is the *only* thing that
reads a client's data, packs it into a plain dict, and hands it over. One
definition of each metric, shared with the dashboard (apps.metrics) — the advisor
and the chart the client sees cannot disagree, because they read the same numbers.

Deterministic and JSON-safe: Decimals and dates become strings so the snapshot
stored on the report is exactly what was sent to the model.
"""

from decimal import Decimal

from apps.metrics import services as metrics


def _jsonable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def build_snapshot(*, client, start=None, end=None):
    """Everything an advisor is allowed to see about ONE client for ONE period.

    Scoped hard to `client`: there is no path here to another client's data.
    """
    snapshot = {
        "client": {"id": client.id, "name": client.name, "kind": client.kind},
        "period": {"start": start, "end": end},
        "herd": metrics.herd_snapshot(client=client),
        "balance": client.account.balance_cached,
        "cost": metrics.cost_breakdown(client=client, start=start, end=end),
        "conversion": metrics.conversion(client=client, start=start, end=end),
        "mortality": metrics.mortality(client=client, start=start, end=end),
        "account": metrics.account_evolution(client=client, start=start, end=end),
        "inconsistencies": metrics.inconsistencies(client=client),
    }
    return _jsonable(snapshot)
