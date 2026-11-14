"""Cliente POWER con httpx mockeado, idempotencia, modo offline y fixture demo."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import pytest

from rastrojo.data.cli import DEMO_END, DEMO_PLOT, DEMO_START
from rastrojo.data.errors import DataError, DataErrorCode
from rastrojo.data.et0 import ET0_VARIABLE
from rastrojo.data.power import PARAMETERS, fetch_power_raw, get_power_daily
from rastrojo.data.settings import DataSettings
from tests.data.conftest import DEMO_FIXTURES, REPO_ROOT, power_mock_handler, synthetic_payload


def _no_sleep(_: float) -> None:
    return None


def test_fetch_splits_in_year_chunks() -> None:
    calls: list[httpx.Request] = []
    with httpx.Client(transport=power_mock_handler(calls)) as client:
        payloads = fetch_power_raw(
            -33.07, -61.12, date(2000, 6, 1), date(2011, 2, 1), client=client, chunk_years=5
        )
    assert len(payloads) == len(calls) == 3
    first = calls[0].url.params
    assert first["community"] == "AG"
    assert first["start"] == "20000601" and first["end"] == "20041231"
    assert set(first["parameters"].split(",")) == set(PARAMETERS)
    assert calls[-1].url.params["end"] == "20110201"


def test_retries_on_server_error_then_succeeds() -> None:
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 3:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json=synthetic_payload(date(2020, 1, 1), date(2020, 1, 2)))

    sleeps: list[float] = []
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        fetch_power_raw(
            -33.07, -61.12, date(2020, 1, 1), date(2020, 1, 2), client=client, sleep=sleeps.append
        )
    assert len(attempts) == 3
    assert sleeps == [1.0, 2.0]


def test_client_error_is_not_retried() -> None:
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        return httpx.Response(422, json={"messages": ["bad parameter"]})

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DataError) as err,
    ):
        fetch_power_raw(
            -33.07, -61.12, date(2020, 1, 1), date(2020, 1, 2), client=client, sleep=_no_sleep
        )
    assert err.value.code is DataErrorCode.UPSTREAM_UNAVAILABLE
    assert len(attempts) == 1


def test_retries_are_bounded_on_transport_errors() -> None:
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        raise httpx.ConnectError("down", request=request)

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(DataError) as err,
    ):
        fetch_power_raw(
            -33.07, -61.12, date(2020, 1, 1), date(2020, 1, 2), client=client, sleep=_no_sleep
        )
    assert err.value.code is DataErrorCode.UPSTREAM_UNAVAILABLE
    assert len(attempts) == 4


def test_second_ingest_uses_cache_without_network(
    settings: DataSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[httpx.Request] = []
    with httpx.Client(transport=power_mock_handler(calls)) as client:
        first = get_power_daily(
            -33.07, -61.12, date(2020, 1, 1), date(2020, 3, 1), settings=settings, client=client
        )
    assert not first.from_cache and len(calls) == 1

    def boom(*args: object, **kwargs: object) -> httpx.Response:
        raise AssertionError("no debe haber red")

    monkeypatch.setattr(httpx.Client, "send", boom)
    second = get_power_daily(
        -33.07000001, -61.12, date(2020, 1, 1), date(2020, 3, 1), settings=settings
    )
    assert second.from_cache
    assert second.content_sha256 == first.content_sha256
    assert len(second.wide()) == 61
    assert list(second.wide().columns) == list(PARAMETERS)


def test_period_before_coverage_fails_before_network(
    settings: DataSettings, no_network: None
) -> None:
    with pytest.raises(DataError) as err:
        get_power_daily(-33.07, -61.12, date(1975, 1, 1), date(1990, 1, 1), settings=settings)
    assert err.value.code is DataErrorCode.PERIOD_OUT_OF_COVERAGE


def test_offline_without_cache_is_data_not_cached(tmp_path: Path, no_network: None) -> None:
    cfg = DataSettings(cache_dir=tmp_path / "c", fixtures_dir=tmp_path / "f", offline=True)
    with pytest.raises(DataError) as err:
        get_power_daily(10.0, 10.0, date(2020, 1, 1), date(2020, 1, 2), settings=cfg)
    assert err.value.code is DataErrorCode.DATA_NOT_CACHED
    assert err.value.details["dataset"] == "NASA_POWER"
    assert err.value.details["start"] == "2020-01-01"


def test_demo_mode_reads_committed_fixture(tmp_path: Path, no_network: None) -> None:
    cfg = DataSettings(cache_dir=tmp_path / "empty", fixtures_dir=DEMO_FIXTURES, demo_mode=True)
    result = get_power_daily(DEMO_PLOT.lat, DEMO_PLOT.lon, DEMO_START, DEMO_END, settings=cfg)
    assert result.from_cache
    wide = result.wide()
    assert len(wide) == (DEMO_END - DEMO_START).days + 1
    assert wide.index.min().date() == DEMO_START and wide.index.max().date() == DEMO_END
    # Radiación: POWER la publica desde 1984; antes queda como hueco explícito.
    by_year = result.missing_by_year()
    assert (by_year.loc[1981:1983, "ALLSKY_SFC_SW_DWN"] > 0).all()
    assert int(by_year.loc[1984:, "ALLSKY_SFC_SW_DWN"].sum()) == 0
    assert int(by_year["PRECTOTCORR"].sum()) == int(result.gaps.missing_by_variable["PRECTOTCORR"])
    et0 = result.et0()
    assert et0["variable"].unique().tolist() == [ET0_VARIABLE]
    assert et0[et0["date"] < "1984-01-01"]["is_missing"].all()
    valid = et0[~et0["is_missing"]]["value"]
    assert (valid >= 0).all()
    assert result.meta["is_modeled"] is True
    assert result.source("PRECTOTCORR").is_modeled is True


def test_fixture_is_small_and_in_repo() -> None:
    files = sorted((DEMO_FIXTURES / "NASA_POWER").glob("*.parquet"))
    assert len(files) == 1
    assert files[0].stat().st_size < 2_000_000
    assert files[0].is_relative_to(REPO_ROOT)
