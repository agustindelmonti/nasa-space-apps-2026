"""Caché parquet + sidecar y esquema pandera."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from rastrojo.data.cache import CachePaths, cache_key, read_cache, write_cache
from rastrojo.data.errors import DataError, DataErrorCode
from rastrojo.data.gaps import gap_report, missing_by_year
from rastrojo.data.power import POWER_SCHEMA, normalize_power
from rastrojo.data.schema import validate_long
from tests.data.conftest import synthetic_payload

START = date(2020, 1, 1)
END = date(2020, 1, 5)


def _frame():  # type: ignore[no-untyped-def]
    payload = synthetic_payload(START, END, overrides={("PRECTOTCORR", "20200103"): -999.0})
    df, _ = normalize_power([payload], START, END)
    return df


def test_coordinates_equivalent_share_key() -> None:
    assert cache_key(-33.04400001, -61.12, START, END) == cache_key(-33.044, -61.12, START, END)
    assert cache_key(-33.044, -61.12, START, END) == "-33.0440_-61.1200_20200101-20200105"


def test_double_write_gives_identical_hash(tmp_path: Path) -> None:
    df = _frame()
    a = CachePaths.build(tmp_path / "a", "NASA_POWER", "k")
    b = CachePaths.build(tmp_path / "b", "NASA_POWER", "k")
    h1 = write_cache(df, a, POWER_SCHEMA, {"retrieved_at": "2026-11-14T10:00:00+00:00"})
    h2 = write_cache(
        df.sample(frac=1, random_state=0), b, POWER_SCHEMA, {"retrieved_at": "2026-11-14T11:00:00"}
    )
    assert h1 == h2
    assert a.parquet.read_bytes() == b.parquet.read_bytes()
    back, meta = read_cache(a, POWER_SCHEMA)
    assert meta["content_sha256"] == h1
    assert back["is_missing"].sum() == 1


def test_corrupt_cache_missing_variable_names_it(tmp_path: Path) -> None:
    df = _frame()
    paths = CachePaths.build(tmp_path, "NASA_POWER", "k")
    write_cache(df, paths, POWER_SCHEMA, {})
    with pytest.raises(DataError) as err:
        validate_long(df[df["variable"] != "T2M_MAX"], POWER_SCHEMA)
    assert err.value.code is DataErrorCode.CACHE_SCHEMA_INVALID
    assert err.value.details["missing_variables"] == ["T2M_MAX"]
    assert "T2M_MAX" in str(err.value)


def test_missing_column_is_rejected() -> None:
    with pytest.raises(DataError) as err:
        validate_long(_frame().drop(columns=["unit"]), POWER_SCHEMA)
    assert err.value.code is DataErrorCode.CACHE_SCHEMA_INVALID
    assert err.value.details["missing_columns"] == ["unit"]


def test_physical_range_violation_reports_range() -> None:
    df = _frame()
    df.loc[df["variable"] == "RH2M", "value"] = 170.0
    with pytest.raises(DataError) as err:
        validate_long(df, POWER_SCHEMA)
    assert err.value.code is DataErrorCode.CACHE_SCHEMA_INVALID
    assert "RH2M fuera del rango físico permitido [0.0, 100.0]" in str(err.value)


def test_inconsistent_missing_flag_is_rejected() -> None:
    df = _frame()
    df.loc[df["missing_reason"].notna(), "missing_reason"] = None
    with pytest.raises(DataError) as err:
        validate_long(df, POWER_SCHEMA)
    assert "is_missing" in str(err.value)


def test_tampered_parquet_fails_hash_check(tmp_path: Path) -> None:
    paths = CachePaths.build(tmp_path, "NASA_POWER", "k")
    write_cache(_frame(), paths, POWER_SCHEMA, {})
    meta = json.loads(paths.meta.read_text())
    meta["content_sha256"] = "0" * 64
    paths.meta.write_text(json.dumps(meta))
    with pytest.raises(DataError) as err:
        read_cache(paths, POWER_SCHEMA)
    assert err.value.code is DataErrorCode.CACHE_SCHEMA_INVALID


def test_gap_report_counts_by_variable_and_year() -> None:
    report = gap_report(_frame(), "NASA_POWER")
    assert report.has_gaps
    assert report.total_days == 5
    assert report.missing_by_variable["PRECTOTCORR"] == 1
    assert report.missing_by_variable["T2M"] == 0
    assert report.missing_by_year[2020]["PRECTOTCORR"] == 1
    assert [(e.variable, e.date, e.reason) for e in report.entries] == [
        ("PRECTOTCORR", date(2020, 1, 3), "FILL_VALUE")
    ]
    table = missing_by_year(_frame())
    assert int(table.loc[2020, "PRECTOTCORR"]) == 1
