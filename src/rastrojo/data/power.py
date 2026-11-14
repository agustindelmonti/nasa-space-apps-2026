"""Adaptador de NASA POWER: serie diaria por punto, comunidad AG.

Separación red / normalización (design, decisión 1): ``fetch_power_raw`` habla con la API
y ``normalize_power`` es pura, testeable con un JSON de muestra sin red.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from functools import cached_property
from typing import Any

import httpx
import pandas as pd

from rastrojo.data.cache import CachePaths, cache_key, find_cached, read_cache, write_cache
from rastrojo.data.errors import DataError, DataErrorCode
from rastrojo.data.et0 import ET0_PROVENANCE, et0_series
from rastrojo.data.gaps import GapReport, gap_report, missing_by_year
from rastrojo.data.schema import DatasetSchemaSpec, MissingReason, VariableSpec
from rastrojo.data.settings import DataSettings
from rastrojo.domain import Dataset, DerivedProvenance, Period, Source

DATASET = Dataset.NASA_POWER.value
POWER_DAILY_POINT_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
COMMUNITY = "AG"
COVERAGE_START = date(1981, 1, 1)
RADIATION_COVERAGE_START = date(1984, 1, 1)  # informado por la propia API en `messages`
DEFAULT_FILL_VALUE = -999.0
DEFAULT_CHUNK_YEARS = 5
DEFAULT_MAX_ATTEMPTS = 4
DEFAULT_TIMEOUT_S = 60.0

# Resolución según la documentación de POWER: meteorología desde MERRA-2 (0.5° x 0.625°)
# y radiación solar desde GEWEX SRB y CERES SYN1deg (1° x 1°), desde 1984.
METEO_RESOLUTION = "0.5° x 0.625° (MERRA-2)"
RADIATION_RESOLUTION = "1° x 1° (GEWEX SRB / CERES SYN1deg según el período)"
TEMPORAL_RESOLUTION = "diaria"
LIMITATION = (
    "Promedio de una celda de decenas de km; lluvia de reanálisis corregida, "
    "no pluviómetro del lote"
)
MERRA2_LAT_STEP = 0.5
MERRA2_LON_STEP = 0.625

# Unidades tal como las publica POWER -> unidad normalizada en caché.
_UNIT_MAP = {"mm/day": "mm/day", "C": "degC", "%": "%", "m/s": "m/s", "kPa": "kPa"}
_UNIT_MAP["MJ/m^2/day"] = "MJ/m2/day"

POWER_SCHEMA = DatasetSchemaSpec(
    dataset=DATASET,
    variables={
        "PRECTOTCORR": VariableSpec("mm/day", 0.0, 500.0),
        "T2M": VariableSpec("degC", -40.0, 60.0),
        "T2M_MIN": VariableSpec("degC", -40.0, 60.0),
        "T2M_MAX": VariableSpec("degC", -40.0, 60.0),
        "ALLSKY_SFC_SW_DWN": VariableSpec("MJ/m2/day", 0.0, 45.0),
        "RH2M": VariableSpec("%", 0.0, 100.0),
        "WS2M": VariableSpec("m/s", 0.0, 50.0),
        "PS": VariableSpec("kPa", 50.0, 110.0),
    },
)
PARAMETERS: tuple[str, ...] = tuple(POWER_SCHEMA.variables)
RADIATION_PARAMETERS = frozenset({"ALLSKY_SFC_SW_DWN"})

Sleeper = Callable[[float], None]


# --- Validación de período y bloques ---------------------------------------------


def check_period(start: date, end: date) -> Period:
    if start < COVERAGE_START:
        raise DataError(
            DataErrorCode.PERIOD_OUT_OF_COVERAGE,
            f"NASA POWER diario cubre desde {COVERAGE_START.isoformat()}; "
            f"se pidió desde {start.isoformat()}",
            dataset=DATASET,
            coverage_start=COVERAGE_START.isoformat(),
            requested_start=start.isoformat(),
        )
    if end < start:
        raise DataError(
            DataErrorCode.PERIOD_OUT_OF_COVERAGE,
            "el período termina antes de empezar",
            dataset=DATASET,
            requested_start=start.isoformat(),
            requested_end=end.isoformat(),
        )
    return Period(start=start, end=end)


def year_chunks(start: date, end: date, chunk_years: int) -> list[tuple[date, date]]:
    """Parte el período en tramos de ``chunk_years`` años calendario."""
    if chunk_years < 1:
        raise ValueError("chunk_years debe ser al menos 1")
    chunks: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(end, date(cursor.year + chunk_years - 1, 12, 31))
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


# --- Red ----------------------------------------------------------------------------


def _is_retryable(status: int) -> bool:
    return status == 429 or status >= 500


def _get_json_with_retries(
    client: httpx.Client,
    params: dict[str, str],
    *,
    max_attempts: int,
    sleep: Sleeper,
) -> dict[str, Any]:
    last_detail = ""
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.get(POWER_DAILY_POINT_URL, params=params)
        except httpx.TransportError as exc:
            last_detail = f"{type(exc).__name__}: {exc}"
        else:
            if response.status_code == 200:
                payload: dict[str, Any] = response.json()
                return payload
            last_detail = f"HTTP {response.status_code}: {response.text[:300]}"
            if not _is_retryable(response.status_code):
                break
        if attempt < max_attempts:
            sleep(float(2 ** (attempt - 1)))
    raise DataError(
        DataErrorCode.UPSTREAM_UNAVAILABLE,
        f"NASA POWER no respondió correctamente: {last_detail}",
        dataset=DATASET,
        params=params,
        attempts=max_attempts,
    )


def fetch_power_raw(
    lat: float,
    lon: float,
    start: date,
    end: date,
    *,
    client: httpx.Client | None = None,
    parameters: Sequence[str] = PARAMETERS,
    chunk_years: int = DEFAULT_CHUNK_YEARS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    sleep: Sleeper = time.sleep,
) -> list[dict[str, Any]]:
    """Baja los JSON crudos de POWER, un pedido por tramo de años."""
    check_period(start, end)
    own_client = client is None
    http = client or httpx.Client(timeout=DEFAULT_TIMEOUT_S)
    try:
        payloads = []
        for chunk_start, chunk_end in year_chunks(start, end, chunk_years):
            params = {
                "parameters": ",".join(parameters),
                "community": COMMUNITY,
                "latitude": f"{lat:.4f}",
                "longitude": f"{lon:.4f}",
                "start": f"{chunk_start:%Y%m%d}",
                "end": f"{chunk_end:%Y%m%d}",
                "format": "JSON",
            }
            payloads.append(
                _get_json_with_retries(http, params, max_attempts=max_attempts, sleep=sleep)
            )
        return payloads
    finally:
        if own_client:
            http.close()


# --- Normalización pura ----------------------------------------------------------------


def _response_meta(payloads: Sequence[dict[str, Any]]) -> dict[str, Any]:
    sources: set[str] = set()
    messages: list[str] = []
    versions: set[str] = set()
    elevations: set[float] = set()
    coords: set[tuple[float, float]] = set()
    for p in payloads:
        header = p.get("header", {})
        sources.update(str(s) for s in header.get("sources", []))
        api = header.get("api", {})
        if "version" in api:
            versions.add(str(api["version"]))
        for m in p.get("messages", []):
            if m not in messages:
                messages.append(str(m))
        geometry = p.get("geometry", {}).get("coordinates", [])
        if len(geometry) >= 2:
            coords.add((float(geometry[1]), float(geometry[0])))
        if len(geometry) >= 3:
            elevations.add(float(geometry[2]))
    return {
        "api_version": sorted(versions),
        "upstream_sources": sorted(sources),
        "messages": messages,
        "returned_point": [list(c) for c in sorted(coords)],
        "elevation_m": sorted(elevations)[0] if len(elevations) == 1 else None,
    }


def normalize_power(
    payloads: Sequence[dict[str, Any]],
    start: date,
    end: date,
    *,
    parameters: Sequence[str] = PARAMETERS,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Convierte respuestas JSON de POWER al frame largo de caché.

    - Valor de relleno (``header.fill_value``, -999 en POWER) -> faltante ``FILL_VALUE``.
    - Fecha o variable ausente de la respuesta -> faltante ``NO_DATA``.
    Ningún faltante se rellena.
    """
    check_period(start, end)
    values: dict[str, dict[str, float]] = {p: {} for p in parameters}
    fill_values: dict[str, float] = {}
    for payload in payloads:
        header = payload.get("header", {})
        fill = float(header.get("fill_value", DEFAULT_FILL_VALUE))
        units_meta = payload.get("parameters", {})
        series = payload.get("properties", {}).get("parameter", {})
        for param in parameters:
            if param not in series:
                continue
            published_unit = units_meta.get(param, {}).get("units")
            expected = POWER_SCHEMA.variables[param].unit
            if published_unit is not None and _UNIT_MAP.get(published_unit) != expected:
                raise DataError(
                    DataErrorCode.UPSTREAM_UNAVAILABLE,
                    f"POWER publicó {param} en '{published_unit}', se esperaba {expected}",
                    dataset=DATASET,
                    variable=param,
                )
            for day_key, raw in series[param].items():
                values[param][str(day_key)] = float(raw) if raw is not None else fill
                fill_values[param] = fill

    days = pd.date_range(start, end, freq="D")
    day_keys = [d.strftime("%Y%m%d") for d in days]
    frames = []
    for param in parameters:
        unit = POWER_SCHEMA.variables[param].unit
        fill = fill_values.get(param, DEFAULT_FILL_VALUE)
        col_values: list[float | None] = []
        reasons: list[str | None] = []
        for key in day_keys:
            raw = values[param].get(key)
            if raw is None:
                col_values.append(None)
                reasons.append(MissingReason.NO_DATA.value)
            elif raw == fill:
                col_values.append(None)
                reasons.append(MissingReason.FILL_VALUE.value)
            else:
                col_values.append(raw)
                reasons.append(None)
        frames.append(
            pd.DataFrame(
                {
                    "date": days.astype("datetime64[ns]"),
                    "variable": pd.Series([param] * len(days), dtype=object),
                    "value": pd.Series(col_values, dtype="float64"),
                    "unit": pd.Series([unit] * len(days), dtype=object),
                    "is_missing": pd.Series([r is not None for r in reasons], dtype=bool),
                    "missing_reason": pd.Series(reasons, dtype=object),
                }
            )
        )
    df = pd.concat(frames, ignore_index=True)
    df = df.sort_values(["variable", "date"], kind="mergesort").reset_index(drop=True)
    return df, _response_meta(payloads)


# --- Celda efectiva y Source ------------------------------------------------------------


def merra2_cell_center(lat: float, lon: float) -> tuple[float, float]:
    """Centro de la celda MERRA-2 (origen -90/-180, paso 0.5° x 0.625°) que contiene el punto."""
    clat = -90.0 + round((lat + 90.0) / MERRA2_LAT_STEP) * MERRA2_LAT_STEP
    clon = -180.0 + round((lon + 180.0) / MERRA2_LON_STEP) * MERRA2_LON_STEP
    return round(clat, 4), round(clon, 4)


def _location_note(lat: float, lon: float, variable: str) -> str:
    if variable in RADIATION_PARAMETERS:
        return f"punto pedido {lat:.4f}, {lon:.4f}; celda de radiación de ~1° que contiene el punto"
    clat, clon = merra2_cell_center(lat, lon)
    return (
        f"punto pedido {lat:.4f}, {lon:.4f}; celda MERRA-2 de 0.5° x 0.625° centrada en "
        f"{clat:.4f}, {clon:.4f} (según la definición de grilla MERRA-2)"
    )


def power_source(variable: str, lat: float, lon: float, period: Period) -> Source:
    if variable not in POWER_SCHEMA.variables:
        raise DataError(
            DataErrorCode.SOURCE_INCOMPLETE,
            f"variable POWER desconocida: {variable}",
            dataset=DATASET,
            variable=variable,
        )
    resolution = RADIATION_RESOLUTION if variable in RADIATION_PARAMETERS else METEO_RESOLUTION
    return Source(
        dataset=Dataset.NASA_POWER,
        variable=variable,
        period=period,
        spatial_resolution=resolution,
        temporal_resolution=TEMPORAL_RESOLUTION,
        is_modeled=True,
        location_note=_location_note(lat, lon, variable),
    )


# --- Resultado e ingesta -----------------------------------------------------------------


@dataclass(frozen=True)
class PowerDaily:
    """Serie POWER de un punto: frame largo validado, metadatos y reporte de huecos."""

    lat: float
    lon: float
    period: Period
    frame: pd.DataFrame = field(repr=False)
    meta: dict[str, Any] = field(repr=False)
    from_cache: bool

    @property
    def content_sha256(self) -> str:
        return str(self.meta["content_sha256"])

    @property
    def elevation_m(self) -> float | None:
        value = self.meta.get("elevation_m")
        return None if value is None else float(value)

    def units(self) -> dict[str, str]:
        return {v: s.unit for v, s in POWER_SCHEMA.variables.items()}

    def wide(self) -> pd.DataFrame:
        """Una fila por día y una columna por variable (NaN donde hay hueco)."""
        table = self.frame.pivot(index="date", columns="variable", values="value")
        table = table.reindex(columns=list(PARAMETERS)).sort_index()
        table.columns.name = None
        return table

    def source(self, variable: str) -> Source:
        return power_source(variable, self.lat, self.lon, self.period)

    @cached_property
    def gaps(self) -> GapReport:
        return gap_report(self.frame, DATASET)

    def missing_by_year(self) -> pd.DataFrame:
        return missing_by_year(self.frame)

    def et0(self) -> pd.DataFrame:
        """ET0 FAO-56 diaria (DERIVED) en formato largo, con huecos ``MISSING_INPUT``."""
        elevation = self.elevation_m
        if elevation is None:
            raise DataError(
                DataErrorCode.SOURCE_INCOMPLETE,
                "la caché de POWER no informa la elevación de la celda; no se puede calcular Rso",
                dataset=DATASET,
            )
        return et0_series(self.wide(), latitude_deg=self.lat, elevation_m=elevation)

    @property
    def et0_provenance(self) -> DerivedProvenance:
        return ET0_PROVENANCE


def _build_meta(
    lat: float, lon: float, period: Period, response_meta: dict[str, Any], retrieved_at: str
) -> dict[str, Any]:
    clat, clon = merra2_cell_center(lat, lon)
    return {
        "dataset": DATASET,
        "endpoint": POWER_DAILY_POINT_URL,
        "query": {
            "community": COMMUNITY,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "start": period.start.isoformat(),
            "end": period.end.isoformat(),
            "parameters": list(PARAMETERS),
        },
        "retrieved_at": retrieved_at,
        "is_modeled": True,
        "spatial_resolution": {
            "meteorology": METEO_RESOLUTION,
            "radiation": RADIATION_RESOLUTION,
        },
        "temporal_resolution": TEMPORAL_RESOLUTION,
        "effective_cell": {
            "meteorology_center": [clat, clon],
            "meteorology_size_deg": [MERRA2_LAT_STEP, MERRA2_LON_STEP],
            "note": "centro calculado con la definición de grilla MERRA-2",
        },
        "limitation": LIMITATION,
        "fill_value": DEFAULT_FILL_VALUE,
        **response_meta,
    }


def get_power_daily(
    lat: float,
    lon: float,
    start: date,
    end: date,
    *,
    settings: DataSettings | None = None,
    client: httpx.Client | None = None,
    chunk_years: int = DEFAULT_CHUNK_YEARS,
    sleep: Sleeper = time.sleep,
) -> PowerDaily:
    """Serie POWER desde caché si existe y es válida; si no, la baja y la cachea.

    En modo offline (``DEMO_MODE`` u ``OFFLINE``) nunca toca la red: si no hay caché
    falla con ``DATA_NOT_CACHED``.
    """
    cfg = settings or DataSettings()
    period = check_period(start, end)
    key = cache_key(lat, lon, start, end)
    cached = find_cached(cfg.read_dirs, DATASET, key)
    if cached is not None:
        frame, meta = read_cache(cached, POWER_SCHEMA)
        return PowerDaily(lat, lon, period, frame, meta, from_cache=True)
    if not cfg.network_allowed:
        raise DataError(
            DataErrorCode.DATA_NOT_CACHED,
            f"no hay caché de {DATASET} para {key} y el modo offline está activo",
            dataset=DATASET,
            lat=round(lat, 4),
            lon=round(lon, 4),
            start=start.isoformat(),
            end=end.isoformat(),
            searched=[str(d) for d in cfg.read_dirs],
        )
    payloads = fetch_power_raw(
        lat, lon, start, end, client=client, chunk_years=chunk_years, sleep=sleep
    )
    frame, response_meta = normalize_power(payloads, start, end)
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    meta = _build_meta(lat, lon, period, response_meta, retrieved_at)
    paths = CachePaths.build(cfg.cache_dir, DATASET, key)
    write_cache(frame, paths, POWER_SCHEMA, meta)
    frame, meta = read_cache(paths, POWER_SCHEMA)
    return PowerDaily(lat, lon, period, frame, meta, from_cache=False)
