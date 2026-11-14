"""Baja SMAP L4 (SPL4SMGP) recortado a la celda de 9 km del lote demo, vía OPeNDAP de Earthdata.

Uso: ``uv run python scripts/fetch_demo_smap.py``

- Busca en CMR (sin login) los granulos 3-horarios del último día disponible.
- Calcula la celda EASE-Grid 2.0 global de 9 km que contiene el lote y pide solo esa celda
  (``sm_rootzone`` y ``sm_rootzone_pctl``) a ``opendap.earthdata.nasa.gov``. El token de
  Earthdata lo agrega el proxy del entorno; el script no lo lee ni lo guarda.
- Escribe ``data/fixtures/demo/SMAP_L4/sm_rootzone_<lat>_<lon>.json`` con el promedio del día,
  cada granulo usado y su procedencia. Ese fixture se commitea para correr sin red.

Requiere el grupo de dependencias ``data`` (httpx, h5py).
"""

from __future__ import annotations

import io
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import h5py
import httpx

from rastrojo.data.cli import DEMO_PLOT

ROOT = Path(__file__).resolve().parents[1]
CMR = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
SHORT_NAME = "SPL4SMGP"

# EASE-Grid 2.0 global, 9 km (EPSG:6933): parámetros publicados por NSIDC.
CELL_M = 9008.055210146
X0 = -17367530.44516138
Y0 = 7314540.83085491
NCOLS, NROWS = 3856, 1624
A = 6378137.0
F = 1 / 298.257223563


def ease2_cell(lat: float, lon: float) -> tuple[int, int]:
    """Fila y columna de la celda EASE-Grid 2.0 de 9 km que contiene (lat, lon)."""
    e2 = 2 * F - F * F
    e = math.sqrt(e2)
    phi_ts = math.radians(30.0)
    k0 = math.cos(phi_ts) / math.sqrt(1 - e2 * math.sin(phi_ts) ** 2)
    s = math.sin(math.radians(lat))
    q = (1 - e2) * (s / (1 - e2 * s * s) - (1 / (2 * e)) * math.log((1 - e * s) / (1 + e * s)))
    x = A * k0 * math.radians(lon)
    y = A * q / (2 * k0)
    col = int((x - X0) // CELL_M)
    row = int((Y0 - y) // CELL_M)
    if not (0 <= row < NROWS and 0 <= col < NCOLS):
        raise ValueError("el punto cae fuera de la grilla EASE-Grid 2.0 global")
    return row, col


def latest_day_granules(client: httpx.Client) -> list[dict[str, str]]:
    resp = client.get(
        CMR, params={"short_name": SHORT_NAME, "sort_key": "-start_date", "page_size": 8}
    )
    resp.raise_for_status()
    items = resp.json()["items"]
    out: list[dict[str, str]] = []
    day = items[0]["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:10]
    for it in items:
        umm = it["umm"]
        start = umm["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
        if start[:10] != day:
            continue
        api = next(
            (u["URL"] for u in umm.get("RelatedUrls", []) if u.get("Type") == "USE SERVICE API"),
            None,
        )
        if api and "opendap.earthdata.nasa.gov" in api:
            out.append({"granule": umm["GranuleUR"], "start": start, "opendap": api})
    return sorted(out, key=lambda g: g["start"])


def cell_values(client: httpx.Client, opendap: str, row: int, col: int) -> dict[str, float]:
    idx = f"%5B{row}:1:{row}%5D%5B{col}:1:{col}%5D"
    ce = ";".join(
        f"{v}{idx}"
        for v in (
            "/Geophysical_Data/sm_rootzone",
            "/Geophysical_Data/sm_rootzone_pctl",
            "/cell_lat",
            "/cell_lon",
        )
    )
    resp = client.get(f"{opendap}.dap.nc4?dap4.ce={ce}", timeout=120)
    resp.raise_for_status()
    with h5py.File(io.BytesIO(resp.content), "r") as f:
        return {
            "sm_rootzone": float(f["Geophysical_Data/sm_rootzone"][0, 0]),
            "sm_rootzone_pctl": float(f["Geophysical_Data/sm_rootzone_pctl"][0, 0]),
            "cell_lat": float(f["cell_lat"][0, 0]),
            "cell_lon": float(f["cell_lon"][0, 0]),
        }


def main() -> int:
    row, col = ease2_cell(DEMO_PLOT.lat, DEMO_PLOT.lon)
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        granules = latest_day_granules(client)
        if not granules:
            raise SystemExit("CMR no devolvió granulos de SPL4SMGP con OPeNDAP")
        rows = []
        for g in granules:
            vals = cell_values(client, g["opendap"], row, col)
            if vals["sm_rootzone"] < 0:
                continue
            rows.append({**g, **vals})
    if not rows:
        raise SystemExit("la celda del lote vino sin datos (fill value) en todos los granulos")
    mean = math.fsum(r["sm_rootzone"] for r in rows) / len(rows)
    pctl = math.fsum(r["sm_rootzone_pctl"] for r in rows) / len(rows)
    out = {
        "dataset": "SMAP_L4",
        "short_name": SHORT_NAME,
        "variable": "sm_rootzone",
        "unit": "m3/m3",
        "lat": DEMO_PLOT.lat,
        "lon": DEMO_PLOT.lon,
        "ease2_row": row,
        "ease2_col": col,
        "cell_lat": rows[0]["cell_lat"],
        "cell_lon": rows[0]["cell_lon"],
        "date": rows[0]["start"][:10],
        "sm_rootzone_daily_mean": round(mean, 4),
        "sm_rootzone_pctl_daily_mean": round(pctl, 1),
        "granules": [
            {
                "granule": r["granule"],
                "start": r["start"],
                "sm_rootzone": round(r["sm_rootzone"], 4),
            }
            for r in rows
        ],
        "fetched_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path = ROOT / "data" / "fixtures" / "demo" / "SMAP_L4"
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"sm_rootzone_{DEMO_PLOT.lat:.4f}_{DEMO_PLOT.lon:.4f}.json"
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                k: out[k]
                for k in (
                    "date",
                    "sm_rootzone_daily_mean",
                    "sm_rootzone_pctl_daily_mean",
                    "cell_lat",
                    "cell_lon",
                )
            }
            | {"granules": len(rows), "path": str(target.relative_to(ROOT))},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
