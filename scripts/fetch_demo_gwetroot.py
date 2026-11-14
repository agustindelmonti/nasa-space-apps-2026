"""Baja NASA POWER GWETROOT (humedad de la zona de raíces, MERRA-2) del lote demo.

Uso: ``uv run python scripts/fetch_demo_gwetroot.py``

GWETROOT es la humedad relativa de la zona de raíces (0 = seco, 1 = saturado) que publica
NASA POWER desde el reanálisis MERRA-2, sin credenciales. El motor la usa como humedad
inicial de cada campaña en lugar del supuesto fijo A-WAT-12.

Escribe ``data/fixtures/demo/NASA_POWER/GWETROOT_<lat>_<lon>_<inicio>-<fin>.json`` con los
valores diarios y su procedencia, que se commitea para correr sin red.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import httpx

from rastrojo.data.cli import DEMO_END, DEMO_PLOT, DEMO_START

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
ROOT = Path(__file__).resolve().parents[1]


def fixture_path(lat: float, lon: float) -> Path:
    name = f"GWETROOT_{lat:.4f}_{lon:.4f}_{DEMO_START:%Y%m%d}-{DEMO_END:%Y%m%d}.json"
    return ROOT / "data" / "fixtures" / "demo" / "NASA_POWER" / name


def main() -> int:
    params = {
        "parameters": "GWETROOT",
        "community": "AG",
        "latitude": f"{DEMO_PLOT.lat:.4f}",
        "longitude": f"{DEMO_PLOT.lon:.4f}",
        "start": f"{DEMO_START:%Y%m%d}",
        "end": f"{DEMO_END:%Y%m%d}",
        "format": "JSON",
    }
    resp = httpx.get(URL, params=params, timeout=120)
    resp.raise_for_status()
    payload = resp.json()
    raw = payload["properties"]["parameter"]["GWETROOT"]
    values = {k: float(v) for k, v in sorted(raw.items()) if v is not None and float(v) >= 0}
    out = {
        "dataset": "NASA_POWER",
        "variable": "GWETROOT",
        "longname": "Root Zone Soil Wetness (MERRA-2)",
        "unit": "fraction",
        "lat": DEMO_PLOT.lat,
        "lon": DEMO_PLOT.lon,
        "start": f"{DEMO_START:%Y-%m-%d}",
        "end": f"{DEMO_END:%Y-%m-%d}",
        "values": values,
    }
    text = json.dumps(out, sort_keys=True, separators=(",", ":"))
    path = fixture_path(DEMO_PLOT.lat, DEMO_PLOT.lon)
    path.write_text(text + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "path": str(path.relative_to(ROOT)),
                "days": len(values),
                "missing": sum(1 for v in raw.values() if v is None or float(v) < 0),
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
