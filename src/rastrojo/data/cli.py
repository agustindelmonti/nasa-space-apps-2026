"""CLI de ingesta: ``uv run python -m rastrojo.data.cli ingest power --plot demo-casilda``."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from rastrojo.data.cache import CachePaths, cache_key
from rastrojo.data.errors import DataError
from rastrojo.data.power import DATASET, PowerDaily, get_power_daily
from rastrojo.data.settings import DataSettings


@dataclass(frozen=True)
class KnownPlot:
    plot_id: str
    lat: float
    lon: float
    assumption_id: str


# Ubicación del lote demo: parcela de ejemplo al sureste de Casilda, ASSUMPTION A-DEMO-01
# (placeholder del equipo, pendiente de confirmar con AFA). Coincide con tests/domain.
DEMO_PLOT = KnownPlot(plot_id="demo-casilda", lat=-33.07, lon=-61.12, assumption_id="A-DEMO-01")
KNOWN_PLOTS = {DEMO_PLOT.plot_id: DEMO_PLOT}

DEMO_START = date(1981, 1, 1)
DEMO_END = date(2025, 12, 31)


def power_summary(result: PowerDaily) -> dict[str, Any]:
    et0 = result.et0()
    et0_valid = et0[~et0["is_missing"]]["value"]
    return {
        "dataset": DATASET,
        "lat": result.lat,
        "lon": result.lon,
        "start": result.period.start.isoformat(),
        "end": result.period.end.isoformat(),
        "from_cache": result.from_cache,
        "rows": int(len(result.frame)),
        "days": result.gaps.total_days,
        "content_sha256": result.content_sha256,
        "missing_by_variable": result.gaps.missing_by_variable,
        "et0_missing_days": int(et0["is_missing"].sum()),
        "et0_negative_days": int((et0_valid < 0).sum()),
        "et0_mean_mm_day": round(float(et0_valid.mean()), 3) if len(et0_valid) else None,
    }


def copy_to_fixtures(result: PowerDaily, settings: DataSettings) -> CachePaths:
    """Copia la entrada de caché (parquet + sidecar) a ``fixtures_dir`` con el mismo layout."""
    key = cache_key(result.lat, result.lon, result.period.start, result.period.end)
    src = CachePaths.build(settings.cache_dir, DATASET, key)
    dst = CachePaths.build(settings.fixtures_dir, DATASET, key)
    if src.parquet.resolve() == dst.parquet.resolve() or (not src.exists() and dst.exists()):
        return dst
    dst.parquet.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src.parquet, dst.parquet)
    shutil.copyfile(src.meta, dst.meta)
    return dst


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="rastrojo.data.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest", help="Ingesta un dataset a la caché local")
    ingest.add_argument("dataset", choices=["power"])
    ingest.add_argument("--plot", choices=sorted(KNOWN_PLOTS))
    ingest.add_argument("--lat", type=float)
    ingest.add_argument("--lon", type=float)
    ingest.add_argument("--start", type=date.fromisoformat, default=DEMO_START)
    ingest.add_argument("--end", type=date.fromisoformat, default=DEMO_END)
    ingest.add_argument(
        "--to-fixtures", action="store_true", help="Copiar el resultado a fixtures_dir"
    )
    args = parser.parse_args(argv)
    if args.plot is None and (args.lat is None or args.lon is None):
        parser.error("indicar --plot o bien --lat y --lon")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.plot is not None:
        plot = KNOWN_PLOTS[args.plot]
        lat, lon = plot.lat, plot.lon
    else:
        lat, lon = args.lat, args.lon
    settings = DataSettings()
    try:
        result = get_power_daily(lat, lon, args.start, args.end, settings=settings)
    except DataError as exc:
        print(json.dumps(exc.to_dict(), ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    summary = power_summary(result)
    if args.to_fixtures:
        dst = copy_to_fixtures(result, settings)
        summary["fixture"] = str(dst.parquet)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
