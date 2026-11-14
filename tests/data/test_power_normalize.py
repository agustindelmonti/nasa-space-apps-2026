"""Normalización pura de respuestas POWER (sin red)."""

from __future__ import annotations

import math
from datetime import date

import pytest

from rastrojo.data.errors import DataError, DataErrorCode
from rastrojo.data.power import (
    PARAMETERS,
    POWER_SCHEMA,
    check_period,
    merra2_cell_center,
    normalize_power,
    power_source,
    year_chunks,
)
from rastrojo.data.schema import validate_long
from rastrojo.domain import Dataset, Period
from tests.data.conftest import load_power_sample, synthetic_payload


def test_real_sample_radiation_fill_before_1984_is_missing() -> None:
    df, meta = normalize_power([load_power_sample()], date(1983, 12, 29), date(1984, 1, 3))
    validate_long(df, POWER_SCHEMA)
    rad = df[df["variable"] == "ALLSKY_SFC_SW_DWN"].set_index("date")
    assert rad.loc["1983-12-31", "is_missing"]
    assert rad.loc["1983-12-31", "missing_reason"] == "FILL_VALUE"
    assert math.isnan(rad.loc["1983-12-31", "value"])
    assert not rad.loc["1984-01-01", "is_missing"]
    assert (df["value"] != -999).all()
    assert meta["elevation_m"] == pytest.approx(76.14)
    assert "MERRA2" in meta["upstream_sources"]


def test_one_row_per_day_and_variable() -> None:
    df, _ = normalize_power([load_power_sample()], date(1983, 12, 29), date(1984, 1, 3))
    assert len(df) == 6 * len(PARAMETERS)
    assert set(df["variable"]) == set(PARAMETERS)


def test_prectotcorr_fill_value_is_gap_not_zero() -> None:
    payload = synthetic_payload(
        date(2020, 1, 1), date(2020, 1, 3), overrides={("PRECTOTCORR", "20200102"): -999.0}
    )
    df, _ = normalize_power([payload], date(2020, 1, 1), date(2020, 1, 3))
    rain = df[df["variable"] == "PRECTOTCORR"].reset_index(drop=True)
    assert rain.loc[1, "is_missing"]
    assert rain.loc[1, "missing_reason"] == "FILL_VALUE"
    assert math.isnan(rain.loc[1, "value"])
    assert rain["value"].dropna().tolist() == [1.0, 1.0]


def test_absent_dates_are_no_data() -> None:
    payload = synthetic_payload(date(2020, 1, 1), date(2020, 1, 2))
    df, _ = normalize_power([payload], date(2020, 1, 1), date(2020, 1, 3))
    last = df[df["date"] == "2020-01-03"]
    assert last["is_missing"].all()
    assert set(last["missing_reason"]) == {"NO_DATA"}


def test_absent_parameter_is_no_data() -> None:
    payload = synthetic_payload(date(2020, 1, 1), date(2020, 1, 2))
    del payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    df, _ = normalize_power([payload], date(2020, 1, 1), date(2020, 1, 2))
    rad = df[df["variable"] == "ALLSKY_SFC_SW_DWN"]
    assert rad["is_missing"].all()
    assert set(rad["missing_reason"]) == {"NO_DATA"}


def test_unexpected_unit_is_rejected() -> None:
    payload = synthetic_payload(date(2020, 1, 1), date(2020, 1, 1))
    payload["parameters"]["ALLSKY_SFC_SW_DWN"]["units"] = "kW-hr/m^2/day"
    with pytest.raises(DataError) as err:
        normalize_power([payload], date(2020, 1, 1), date(2020, 1, 1))
    assert err.value.code is DataErrorCode.UPSTREAM_UNAVAILABLE


def test_period_before_1981_rejected() -> None:
    with pytest.raises(DataError) as err:
        check_period(date(1975, 1, 1), date(1980, 12, 31))
    assert err.value.code is DataErrorCode.PERIOD_OUT_OF_COVERAGE
    assert err.value.details["coverage_start"] == "1981-01-01"


def test_year_chunks_cover_period_without_overlap() -> None:
    chunks = year_chunks(date(1981, 1, 1), date(2025, 12, 31), 5)
    assert len(chunks) == 9
    assert chunks[0] == (date(1981, 1, 1), date(1985, 12, 31))
    assert chunks[-1] == (date(2021, 1, 1), date(2025, 12, 31))
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:], strict=False):
        assert (next_start - prev_end).days == 1


def test_source_records_requested_point_and_cell() -> None:
    period = Period(start=date(1981, 1, 1), end=date(2025, 12, 31))
    src = power_source("T2M_MAX", -33.07, -61.12, period)
    assert src.dataset is Dataset.NASA_POWER
    assert src.is_modeled is True
    assert src.temporal_resolution == "diaria"
    assert "0.5° x 0.625°" in src.spatial_resolution
    assert src.location_note is not None
    assert "-33.0700, -61.1200" in src.location_note
    assert "-33.0000, -61.2500" in src.location_note
    assert merra2_cell_center(-33.07, -61.12) == (-33.0, -61.25)


def test_unknown_variable_source_is_blocked() -> None:
    period = Period(start=date(1981, 1, 1), end=date(1981, 1, 2))
    with pytest.raises(DataError) as err:
        power_source("FOO", -33.07, -61.12, period)
    assert err.value.code is DataErrorCode.SOURCE_INCOMPLETE
