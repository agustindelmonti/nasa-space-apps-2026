"""Baja la lluvia diaria GPM IMERG Final (GPM_3IMERGDF v07) del punto del lote demo.

Uso: ``uv run python scripts/fetch_demo_imerg.py [--workers 16]``

- Lista en CMR (sin login) todos los granulos diarios (uno por día desde junio de 2000).
- Por cada día pide a ``opendap.earthdata.nasa.gov`` solo la celda de 0,1° del lote
  (variable ``precipitation``, mm/día). Token: ``EARTHDATA_TOKEN`` si existe, enviado solo a
  ese host; si no, lo agrega el proxy del entorno. Requiere haber autorizado la aplicación
  "NASA GESDISC DATA ARCHIVE" en el perfil de Earthdata.
- Incremental: lee el fixture existente y solo pide los días que faltan.
- Escribe ``data/fixtures/demo/GPM_IMERG/precip_<lat>_<lon>.json``. Requiere el grupo ``data``.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import h5py
import httpx

from rastrojo.data.cli import DEMO_PLOT

ROOT = Path(__file__).resolve().parents[1]
CMR = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
SHORT_NAME = "GPM_3IMERGDF"
VERSION = "07"
OPENDAP = "https://opendap.earthdata.nasa.gov/collections/{cid}/granules/{gid}"


def fixture_path() -> Path:
    return (
        ROOT
        / "data"
        / "fixtures"
        / "demo"
        / "GPM_IMERG"
        / f"precip_{DEMO_PLOT.lat:.4f}_{DEMO_PLOT.lon:.4f}.json"
    )


def list_granules(client: httpx.Client) -> list[tuple[str, str, str]]:
    """(día ISO, concept id de la colección, GranuleUR) de todos los granulos diarios."""
    out: list[tuple[str, str, str]] = []
    headers: dict[str, str] = {}
    while True:
        resp = client.get(
            CMR,
            params={
                "short_name": SHORT_NAME,
                "version": VERSION,
                "page_size": 2000,
                "sort_key": "start_date",
            },
            headers=headers,
        )
        resp.raise_for_status()
        items = resp.json()["items"]
        for it in items:
            umm = it["umm"]
            day = umm["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"][:10]
            out.append((day, it["meta"]["collection-concept-id"], umm["GranuleUR"]))
        after = resp.headers.get("CMR-Search-After")
        if not items or not after:
            break
        headers = {"CMR-Search-After": after}
    return out


def cell_index(lat: float, lon: float) -> tuple[int, int]:
    """Índices (lon, lat) de la grilla global IMERG de 0,1° (centros en -179,95 y -89,95)."""
    return int((lon + 180.0) // 0.1), int((lat + 90.0) // 0.1)


def fetch_day(client: httpx.Client, cid: str, gid: str, ilon: int, ilat: int) -> float:
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = OPENDAP.format(cid=cid, gid=quote(gid, safe=""))
    ce = f"/precipitation%5B0%5D%5B{ilon}%5D%5B{ilat}%5D;/lat%5B{ilat}%5D;/lon%5B{ilon}%5D"
    # GES DISC devuelve 403 o 5xx sueltos bajo carga: reintentar con espera creciente.
    for attempt in range(5):
        resp = client.get(f"{url}.dap.nc4?dap4.ce={ce}", headers=headers, timeout=120)
        if resp.status_code < 500 and resp.status_code != 403:
            break
        time.sleep(2 * (attempt + 1))
    resp.raise_for_status()
    with h5py.File(io.BytesIO(resp.content), "r") as f:
        value = float(f["precipitation"][()].ravel()[0])
        lat = float(f["lat"][()].ravel()[0])
        lon = float(f["lon"][()].ravel()[0])
    if abs(lat - DEMO_PLOT.lat) > 0.1 or abs(lon - DEMO_PLOT.lon) > 0.1:
        raise SystemExit(f"la celda pedida ({lat}, {lon}) no contiene al lote: revisar índices")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--limit", type=int, default=0, help="solo los primeros N días faltantes")
    args = parser.parse_args()

    path = fixture_path()
    existing: dict[str, float] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))["values"]
    ilon, ilat = cell_index(DEMO_PLOT.lat, DEMO_PLOT.lon)
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        granules = list_granules(client)
        todo = [g for g in granules if g[0].replace("-", "") not in existing]
        if args.limit:
            todo = todo[: args.limit]
        values = dict(existing)
        failed: list[str] = []
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {
                pool.submit(fetch_day, client, cid, gid, ilon, ilat): day for day, cid, gid in todo
            }
            for n, fut in enumerate(as_completed(futures), 1):
                day = futures[fut]
                try:
                    v = fut.result()
                except Exception as exc:  # noqa: BLE001 - se reporta y sigue
                    failed.append(f"{day}: {exc}")
                    continue
                if v >= 0:
                    values[day.replace("-", "")] = round(v, 3)
                if n % 500 == 0:
                    print(f"{n}/{len(todo)} días", flush=True)
    out = {
        "dataset": "GPM_IMERG",
        "short_name": SHORT_NAME,
        "version": VERSION,
        "variable": "precipitation",
        "unit": "mm/day",
        "lat": DEMO_PLOT.lat,
        "lon": DEMO_PLOT.lon,
        "grid_index": {"lon": ilon, "lat": ilat},
        "values": dict(sorted(values.items())),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    keys = sorted(values)
    print(
        json.dumps(
            {
                "days": len(values),
                "new": len(values) - len(existing),
                "failed": len(failed),
                "first": keys[0] if keys else None,
                "last": keys[-1] if keys else None,
                "failed_sample": failed[:3],
            },
            indent=2,
        )
    )
    return 1 if failed and len(failed) > len(todo) // 10 else 0


if __name__ == "__main__":
    raise SystemExit(main())
