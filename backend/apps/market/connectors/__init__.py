"""Connector registry. `manual` is intentionally absent — it has no connector."""

from apps.market.connectors.canuelas import CanuelasConnector
from apps.market.connectors.ipcva import IpcvaConnector

CONNECTORS = {c.slug: c for c in (CanuelasConnector, IpcvaConnector)}


def get_connector(slug):
    """Return a connector instance for the slug, or None if the source is manual."""
    cls = CONNECTORS.get(slug)
    return cls() if cls else None
