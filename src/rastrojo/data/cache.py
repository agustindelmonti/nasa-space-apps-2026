"""Caché parquet + sidecar JSON, determinista y validada por esquema.

El parquet se escribe con opciones fijas (sin índice de pandas, zstd nivel fijo, filas
ordenadas por variable y fecha, esquema arrow explícito) para que el mismo contenido dé
los mismos bytes y por lo tanto el mismo ``content_sha256``. La fecha de descarga va solo
en el sidecar ``<clave>.meta.json``.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Final

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from rastrojo.data.errors import DataError, DataErrorCode
from rastrojo.data.schema import LONG_COLUMNS, DatasetSchemaSpec, validate_long

COORD_DECIMALS = 4
PARQUET_COMPRESSION: Final = "zstd"
PARQUET_COMPRESSION_LEVEL = 9
CACHE_FORMAT_VERSION = 1

_ARROW_FIELDS: list[pa.Field[Any]] = [
    pa.field("date", pa.date32(), nullable=False),
    pa.field("variable", pa.string(), nullable=False),
    pa.field("value", pa.float64(), nullable=True),
    pa.field("unit", pa.string(), nullable=False),
    pa.field("is_missing", pa.bool_(), nullable=False),
    pa.field("missing_reason", pa.string(), nullable=True),
]
ARROW_SCHEMA = pa.schema(_ARROW_FIELDS)


def normalize_coord(value: float) -> str:
    """Coordenada con precisión fija (4 decimales, ~11 m) para formar la clave."""
    text = f"{round(value, COORD_DECIMALS):.{COORD_DECIMALS}f}"
    return "0.0000" if text == "-0.0000" else text


def cache_key(lat: float, lon: float, start: date, end: date) -> str:
    return f"{normalize_coord(lat)}_{normalize_coord(lon)}_{start:%Y%m%d}-{end:%Y%m%d}"


@dataclass(frozen=True)
class CachePaths:
    parquet: Path
    meta: Path

    @classmethod
    def build(cls, base_dir: Path, dataset: str, key: str) -> CachePaths:
        folder = base_dir / dataset
        return cls(parquet=folder / f"{key}.parquet", meta=folder / f"{key}.meta.json")

    def exists(self) -> bool:
        return self.parquet.is_file() and self.meta.is_file()


def find_cached(dirs: Iterable[Path], dataset: str, key: str) -> CachePaths | None:
    for base in dirs:
        paths = CachePaths.build(base, dataset, key)
        if paths.exists():
            return paths
    return None


def _to_arrow(df: pd.DataFrame) -> pa.Table:
    ordered = df.sort_values(["variable", "date"], kind="mergesort").reset_index(drop=True)
    dates = [ts.date() for ts in pd.to_datetime(ordered["date"])]
    reasons = [None if pd.isna(r) else str(r) for r in ordered["missing_reason"]]
    values = [None if pd.isna(v) else float(v) for v in ordered["value"]]
    arrays: list[pa.Array[Any]] = [
        pa.array(dates, type=pa.date32()),
        pa.array(ordered["variable"].astype(str).tolist(), type=pa.string()),
        pa.array(values, type=pa.float64()),
        pa.array(ordered["unit"].astype(str).tolist(), type=pa.string()),
        pa.array(ordered["is_missing"].astype(bool).tolist(), type=pa.bool_()),
        pa.array(reasons, type=pa.string()),
    ]
    return pa.Table.from_arrays(arrays, schema=ARROW_SCHEMA)


def frame_from_arrow(table: pa.Table) -> pd.DataFrame:
    """Convierte la tabla arrow al frame largo con tipos estables."""
    missing = [c for c in LONG_COLUMNS if c not in table.column_names]
    if missing:
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"faltan columnas en la caché: {', '.join(missing)}",
            missing_columns=missing,
        )
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(pd.Series(table.column("date").to_pylist())).astype(
                "datetime64[ns]"
            ),
            "variable": pd.Series(table.column("variable").to_pylist(), dtype=object),
            "value": pd.Series(table.column("value").to_pylist(), dtype="float64"),
            "unit": pd.Series(table.column("unit").to_pylist(), dtype=object),
            "is_missing": pd.Series(table.column("is_missing").to_pylist(), dtype=bool),
            "missing_reason": pd.Series(table.column("missing_reason").to_pylist(), dtype=object),
        }
    )
    return df


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def write_cache(
    df: pd.DataFrame, paths: CachePaths, spec: DatasetSchemaSpec, meta: dict[str, Any]
) -> str:
    """Valida, escribe parquet + sidecar y devuelve el ``content_sha256``."""
    validate_long(df, spec)
    table = _to_arrow(df)
    paths.parquet.parent.mkdir(parents=True, exist_ok=True)
    tmp = paths.parquet.with_suffix(".parquet.tmp")
    pq.write_table(
        table,
        tmp,
        compression=PARQUET_COMPRESSION,
        compression_level=PARQUET_COMPRESSION_LEVEL,
        use_dictionary=True,
        write_statistics=True,
    )
    os.replace(tmp, paths.parquet)
    digest = sha256_file(paths.parquet)
    sidecar = dict(meta)
    sidecar["cache_format_version"] = CACHE_FORMAT_VERSION
    sidecar["content_sha256"] = digest
    sidecar["rows"] = table.num_rows
    text = json.dumps(sidecar, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    _atomic_write_bytes(paths.meta, text.encode("utf-8"))
    return digest


def read_meta(paths: CachePaths) -> dict[str, Any]:
    try:
        meta: dict[str, Any] = json.loads(paths.meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"sidecar ilegible: {paths.meta}",
            path=str(paths.meta),
        ) from exc
    return meta


def read_cache(paths: CachePaths, spec: DatasetSchemaSpec) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Lee y valida una entrada de caché (hash del contenido y esquema)."""
    meta = read_meta(paths)
    digest = sha256_file(paths.parquet)
    if meta.get("content_sha256") != digest:
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"el hash del parquet no coincide con el sidecar: {paths.parquet}",
            path=str(paths.parquet),
            expected=meta.get("content_sha256"),
            actual=digest,
        )
    try:
        table = pq.read_table(paths.parquet)
    except (OSError, pa.ArrowException) as exc:
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"parquet ilegible: {paths.parquet}",
            path=str(paths.parquet),
        ) from exc
    df = frame_from_arrow(table)
    validate_long(df, spec)
    return df, meta
