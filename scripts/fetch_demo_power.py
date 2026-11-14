"""Baja NASA POWER 1981-2025 del lote demo, lo cachea y genera el fixture de DEMO_MODE.

Uso: ``uv run python scripts/fetch_demo_power.py``

- Caché cruda: ``data/cache/NASA_POWER/<lat>_<lon>_<inicio>-<fin>.parquet`` (+ ``.meta.json``),
  ignorada por git.
- Fixture: la misma entrada copiada a ``data/fixtures/demo/NASA_POWER/`` (parquet zstd
  validado + sidecar con hash), que se commitea y que lee ``DEMO_MODE=1`` sin red.

La ubicación del lote es ASSUMPTION A-DEMO-01 (ver ``rastrojo.data.cli.DEMO_PLOT``).
Correrlo dos veces no vuelve a descargar: la segunda lee la caché y el hash es el mismo.
"""

from __future__ import annotations

import json

from rastrojo.data.cli import DEMO_END, DEMO_PLOT, DEMO_START, copy_to_fixtures, power_summary
from rastrojo.data.power import get_power_daily
from rastrojo.data.settings import DataSettings


def main() -> int:
    settings = DataSettings()
    result = get_power_daily(DEMO_PLOT.lat, DEMO_PLOT.lon, DEMO_START, DEMO_END, settings=settings)
    fixture = copy_to_fixtures(result, settings)
    summary = power_summary(result)
    summary["plot_id"] = DEMO_PLOT.plot_id
    summary["location_assumption_id"] = DEMO_PLOT.assumption_id
    summary["fixture"] = str(fixture.parquet)
    summary["fixture_bytes"] = fixture.parquet.stat().st_size
    years_with_gaps = {
        str(year): {k: v for k, v in counts.items() if v}
        for year, counts in result.gaps.missing_by_year.items()
        if any(counts.values())
    }
    summary["years_with_gaps"] = years_with_gaps
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
