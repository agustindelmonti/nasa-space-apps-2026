"""Utilidades de tests de la capa de datos (sin red)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from rastrojo.data.power import PARAMETERS
from rastrojo.data.settings import DataSettings

REPO_ROOT = Path(__file__).resolve().parents[2]
POWER_SAMPLE = REPO_ROOT / "tests/fixtures/power/daily_point_19831229_19840103.json"
DEMO_FIXTURES = REPO_ROOT / "data/fixtures/demo"

UNITS = {
    "PRECTOTCORR": "mm/day",
    "T2M": "C",
    "T2M_MIN": "C",
    "T2M_MAX": "C",
    "ALLSKY_SFC_SW_DWN": "MJ/m^2/day",
    "RH2M": "%",
    "WS2M": "m/s",
    "PS": "kPa",
}

# Valores sintéticos SOLO para tests de forma y huecos (no son datos del lote).
SYNTHETIC_DAY = {
    "PRECTOTCORR": 1.0,
    "T2M": 20.0,
    "T2M_MIN": 14.0,
    "T2M_MAX": 26.0,
    "ALLSKY_SFC_SW_DWN": 20.0,
    "RH2M": 60.0,
    "WS2M": 2.0,
    "PS": 100.0,
}


def load_power_sample() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(POWER_SAMPLE.read_text(encoding="utf-8"))
    return data


def synthetic_payload(
    start: date, end: date, overrides: dict[tuple[str, str], float] | None = None
) -> dict[str, Any]:
    """Respuesta con la forma de la API de POWER y valores sintéticos constantes."""
    days = []
    cursor = start
    while cursor <= end:
        days.append(cursor.strftime("%Y%m%d"))
        cursor += timedelta(days=1)
    series = {p: {d: SYNTHETIC_DAY[p] for d in days} for p in PARAMETERS}
    for (param, day), value in (overrides or {}).items():
        series[param][day] = value
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [-61.12, -33.07, 76.14]},
        "properties": {"parameter": series},
        "header": {
            "api": {"version": "test", "name": "POWER Daily API"},
            "sources": ["MERRA2", "POWER"],
            "fill_value": -999.0,
            "start": days[0],
            "end": days[-1],
        },
        "messages": [],
        "parameters": {p: {"units": UNITS[p]} for p in PARAMETERS},
    }


def power_mock_handler(calls: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        start = date.fromisoformat(_iso(request.url.params["start"]))
        end = date.fromisoformat(_iso(request.url.params["end"]))
        return httpx.Response(200, json=synthetic_payload(start, end))

    return httpx.MockTransport(handler)


def _iso(compact: str) -> str:
    return f"{compact[:4]}-{compact[4:6]}-{compact[6:]}"


@pytest.fixture
def settings(tmp_path: Path) -> DataSettings:
    return DataSettings(cache_dir=tmp_path / "cache", fixtures_dir=tmp_path / "fixtures")


@pytest.fixture
def no_network(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Cualquier intento de red con httpx falla el test."""

    def boom(*args: object, **kwargs: object) -> httpx.Response:
        raise AssertionError("intento de red en un test que no debe usar red")

    monkeypatch.setattr(httpx.Client, "send", boom)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", boom)
    yield
