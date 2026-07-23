"""IPCVA — second automated source (docs/feedlot/06c).

Chosen over ROSGAN because its stat pages are server-rendered rather than built
in the browser. BUT the "Precios en Pie" view is a chart builder: the numbers
arrive via an AJAX call when the filters (fecha, categoría, país) are applied, so
they are NOT in the page HTML. The exact data endpoint must be captured with the
network inspector against the live site (do this in Claude Code).

This connector is deliberately a documented stub: `parse` works against whatever
payload the data endpoint returns once its shape is known, and `fetch` raises a
clear error until that endpoint is wired. The point is that the framework already
isolates this source's failure — an un-wired IPCVA never blocks Cañuelas.

Filters observed on the page, for when the endpoint is wired:
  categorías: Novillos, Novillitos, Toros, Vacas, Vaquillonas, Terneros, Terneras
  país: ARGENTINA (entre otros)
  período: mensual, 2004→actual
"""

from datetime import date

from apps.market.connectors.base import BaseConnector, ConnectorError, ParsedPrice

STATS_URL = "https://ipcva.agrositio.com/estadisticas/vista_precios2.php?id=1"


class IpcvaConnector(BaseConnector):
    slug = "ipcva"

    def fetch(self, *, target_date: date) -> bytes:  # pragma: no cover - not wired yet
        raise ConnectorError(
            "IPCVA: el endpoint de datos aún no está cableado. Capturar la llamada AJAX "
            "de 'Precios en Pie' con el inspector de red (Claude Code) y completar fetch()."
        )

    def parse(self, payload: bytes, *, target_date: date) -> list[ParsedPrice]:
        """Wire this once the data endpoint's shape (JSON/XML) is known.

        Left unimplemented on purpose rather than guessing a format: a parser built
        against an imagined payload would pass its own tests and fail on real data.
        """
        raise ConnectorError("IPCVA: parse() pendiente hasta conocer el formato del endpoint.")
