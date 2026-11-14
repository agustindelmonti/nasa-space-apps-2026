"""Baja la anomalía de agua total de GRACE/GRACE-FO (mascons JPL RL06.3 CRI) para el lote demo.

Uso: ``uv run python scripts/fetch_demo_grace.py``

PO.DAAC publica los mascons como un único NetCDF global (unos 260 MB) sin OPeNDAP. El script
lee solo lo que necesita con pedidos HTTP Range: los ejes y la serie de la celda de 0,5° que
contiene el lote. Token de Earthdata: ``EARTHDATA_TOKEN`` si existe (Actions o ``.env``),
enviado solo a ``archive.podaac.earthdata.nasa.gov``; si no, lo agrega el proxy del entorno.

Escribe ``data/fixtures/demo/GRACE_FO/tws_<lat>_<lon>.json`` con la serie mensual en mm, la
media de los últimos 3 meses y su percentil en el registro. Requiere el grupo ``data``.
"""

from __future__ import annotations

import io
import json
import math
import os
from datetime import date, timedelta
from pathlib import Path

import h5py
import httpx

from rastrojo.data.cli import DEMO_PLOT

ROOT = Path(__file__).resolve().parents[1]
CMR = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
SHORT_NAME = "TELLUS_GRAC-GRFO_MASCON_CRI_GRID_RL06.3_V4"
ARCHIVE_HOST = "archive.podaac.earthdata.nasa.gov"
BLOCK = 1 << 20  # 1 MiB por pedido


class HttpRangeFile(io.RawIOBase):
    """Archivo remoto de solo lectura sobre HTTP Range, con caché por bloques."""

    def __init__(self, client: httpx.Client, url: str) -> None:
        self.client = client
        self.url = url
        head = client.get(url, headers={"Range": "bytes=0-0"})
        head.raise_for_status()
        self.size = int(head.headers["Content-Range"].split("/")[1])
        self.pos = 0
        self.cache: dict[int, bytes] = {}
        self.requests = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = max(0, base + offset)
        return self.pos

    def _block(self, n: int) -> bytes:
        if n not in self.cache:
            start = n * BLOCK
            end = min(self.size, start + BLOCK) - 1
            resp = self.client.get(self.url, headers={"Range": f"bytes={start}-{end}"})
            resp.raise_for_status()
            self.cache[n] = resp.content
            self.requests += 1
        return self.cache[n]

    def readinto(self, buf: bytearray | memoryview) -> int:  # type: ignore[override]
        want = min(len(buf), self.size - self.pos)
        got = 0
        while got < want:
            n, off = divmod(self.pos + got, BLOCK)
            chunk = self._block(n)[off : off + want - got]
            buf[got : got + len(chunk)] = chunk
            got += len(chunk)
        self.pos += got
        return got


def latest_granule(client: httpx.Client) -> tuple[str, str]:
    resp = client.get(CMR, params={"short_name": SHORT_NAME, "sort_key": "-start_date"})
    resp.raise_for_status()
    umm = resp.json()["items"][0]["umm"]
    url = next(
        u["URL"]
        for u in umm["RelatedUrls"]
        if u.get("Type") == "GET DATA"
        and u["URL"].startswith("https://")
        and u["URL"].endswith(".nc")
    )
    return umm["GranuleUR"], url


def signed_url(url: str) -> str:
    """PO.DAAC responde 303 a una URL firmada del CDN; esa es la que admite Range."""
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with httpx.Client(timeout=60, follow_redirects=False) as c:
        resp = c.get(url, headers=headers)
    if resp.status_code not in (301, 302, 303, 307):
        raise SystemExit(f"PO.DAAC no redirigió (HTTP {resp.status_code}): ¿token válido?")
    return resp.headers["location"]


def nearest(values: list[float], target: float) -> int:
    return min(range(len(values)), key=lambda i: abs(values[i] - target))


def percentile_rank(series: list[float], x: float) -> float:
    return 100.0 * sum(1 for v in series if v <= x) / len(series)


def main() -> int:
    with httpx.Client(timeout=120, follow_redirects=True) as client:
        granule, url = latest_granule(client)
        remote = HttpRangeFile(client, signed_url(url))
        with h5py.File(io.BufferedReader(remote, buffer_size=BLOCK), "r") as f:
            lat = [float(v) for v in f["lat"][()]]
            lon = [float(v) for v in f["lon"][()]]
            days = [float(v) for v in f["time"][()]]
            time_units = f["time"].attrs.get("units", b"days since 2002-01-01T00:00:00Z")
            lon360 = DEMO_PLOT.lon % 360.0
            i, j = nearest(lat, DEMO_PLOT.lat), nearest(lon, lon360)
            series_cm = [float(v) for v in f["lwe_thickness"][:, i, j]]
    units = time_units.decode() if isinstance(time_units, bytes) else str(time_units)
    origin = date.fromisoformat(units.split("since")[1].strip()[:10])
    months = [
        {"date": (origin + timedelta(days=d)).isoformat(), "tws_mm": round(v * 10.0, 1)}
        for d, v in zip(days, series_cm, strict=True)
        if math.isfinite(v)
    ]
    values = [m["tws_mm"] for m in months]
    last3 = values[-3:]
    mean3 = math.fsum(last3) / len(last3)
    out = {
        "dataset": "GRACE_FO",
        "short_name": SHORT_NAME,
        "granule": granule,
        "variable": "lwe_thickness",
        "unit": "mm",
        "baseline": "anomalía respecto de la media 2004.0-2009.999 (JPL)",
        "lat": DEMO_PLOT.lat,
        "lon": DEMO_PLOT.lon,
        "cell_lat": lat[i],
        "cell_lon": lon[j] - 360.0 if lon[j] > 180 else lon[j],
        "latest_month": months[-1]["date"],
        "latest_tws_mm": values[-1],
        "last3_mean_mm": round(mean3, 1),
        "last3_percentile": round(percentile_rank(values, mean3), 1),
        "months": months,
    }
    path = ROOT / "data" / "fixtures" / "demo" / "GRACE_FO"
    path.mkdir(parents=True, exist_ok=True)
    target = path / f"tws_{DEMO_PLOT.lat:.4f}_{DEMO_PLOT.lon:.4f}.json"
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        k: out[k]
        for k in (
            "latest_month",
            "latest_tws_mm",
            "last3_mean_mm",
            "last3_percentile",
            "cell_lat",
            "cell_lon",
        )
    }
    summary |= {
        "months": len(months),
        "range_requests": remote.requests,
        "path": str(target.relative_to(ROOT)),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
