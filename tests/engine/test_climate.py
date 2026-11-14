from __future__ import annotations

import json
from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from rastrojo.domain import Dataset, Period, Source, YearClass, canonical_json
from rastrojo.engine.climate import (
    ClassificationConfig,
    ClimateClassificationError,
    ClimateErrorCode,
    ExclusionReason,
    RainDay,
    RainSeries,
    WindowDef,
    build_scenarios,
    classify_totals,
    classify_window,
    window_totals,
)

WINTER = WindowDef(name="WINTER", start_month=5, start_day=1, end_month=10, end_day=31)
SUMMER = WindowDef(
    name="SUMMER", start_month=11, start_day=1, end_month=3, end_day=31, crosses_year=True
)
CFG = ClassificationConfig(winter=WINTER, summer=SUMMER, max_missing_days=0, min_years=15)
CFG_SHORT = CFG.model_copy(update={"min_years": 10})


def source(ds: Dataset = Dataset.NASA_POWER) -> Source:
    return Source(
        dataset=ds,
        variable="PRECTOTCORR",
        period=Period(start=date(1981, 1, 1), end=date(2025, 12, 31)),
        spatial_resolution="0.5° x 0.625°",
        temporal_resolution="diaria",
        is_modeled=True,
    )


def series(
    start: date, end: date, mm_fn=lambda d: 1.0 + (d.year % 7) * 0.3 + d.month * 0.01, gaps=()
):
    days = []
    d = start
    while d <= end:
        days.append(RainDay(day=d, mm=None if d in gaps else mm_fn(d), dataset=Dataset.NASA_POWER))
        d += timedelta(days=1)
    return RainSeries(source=source(), days=tuple(days))


def test_window_rejects_extra_and_inverted() -> None:
    with pytest.raises(ValidationError):
        WindowDef.model_validate({**WINTER.model_dump(), "foo": 1})
    with pytest.raises(ValidationError):
        WindowDef(name="WINTER", start_month=10, start_day=31, end_month=10, end_day=1)


def test_summer_crosses_year() -> None:
    assert SUMMER.bounds(2008) == (date(2008, 11, 1), date(2009, 3, 31))


def test_window_changed_by_agronomists() -> None:
    w2 = WINTER.model_copy(update={"end_month": 9, "end_day": 30})
    s = series(date(2000, 1, 1), date(2001, 12, 31), mm_fn=lambda d: 1.0)
    t1, _ = window_totals(s, WINTER, 0)
    t2, _ = window_totals(s, w2, 0)
    assert t1[2000] == 184.0 and t2[2000] == 153.0


def test_leap_year() -> None:
    s = series(date(2007, 1, 1), date(2008, 12, 31), mm_fn=lambda d: 1.0)
    totals, exc = window_totals(s, SUMMER, 0)
    assert totals[2007] == 152.0  # 1/11/2007 a 31/3/2008, con 29/2


def test_missing_days_excluded() -> None:
    gaps = {date(1995, 6, 1), date(1995, 6, 2), date(1995, 6, 3)}
    s = series(date(1994, 1, 1), date(1996, 12, 31), gaps=gaps)
    totals, exc = window_totals(s, WINTER, 0)
    assert 1995 not in totals
    e = [x for x in exc if x.campaign_year == 1995][0]
    assert e.reason is ExclusionReason.MISSING_DAYS and e.missing_days == 3


def test_ongoing_campaign_excluded() -> None:
    s = series(date(2024, 1, 1), date(2026, 11, 10))
    _, exc = window_totals(s, SUMMER, 0)
    assert any(
        e.campaign_year == 2026 and e.reason is ExclusionReason.INCOMPLETE_WINDOW for e in exc
    )


def test_mixed_sources_rejected() -> None:
    s = series(date(2000, 1, 1), date(2000, 12, 31))
    bad = s.model_copy(
        update={
            "days": s.days[:-1]
            + (RainDay(day=date(2000, 12, 31), mm=1.0, dataset=Dataset.GPM_IMERG),)
        }
    )
    with pytest.raises(ClimateClassificationError) as err:
        window_totals(bad, WINTER, 0)
    assert err.value.code is ClimateErrorCode.MIXED_SOURCES


def _totals(n: int) -> dict[int, float]:
    return {1990 + i: 100.0 + 7.0 * ((i * 11) % n) for i in range(n)}


def test_n_divisible_by_three() -> None:
    r = classify_totals(_totals(30), "WINTER", 15, ("x",))
    counts = {c: sum(1 for y in r.years if y.year_class is c) for c in YearClass}
    assert counts == {YearClass.DRY: 10, YearClass.NORMAL: 10, YearClass.WET: 10}
    lowest = sorted(_totals(30).items(), key=lambda kv: kv[1])[:10]
    assert {y for y, _ in lowest} == {
        y.campaign_year for y in r.years if y.year_class is YearClass.DRY
    }


def test_remainder_to_normal_and_weights() -> None:
    r = classify_totals(_totals(31), "WINTER", 15, ("x",))
    counts = {c: sum(1 for y in r.years if y.year_class is c) for c in YearClass}
    assert counts == {YearClass.DRY: 10, YearClass.NORMAL: 11, YearClass.WET: 10}
    assert r.weight == pytest.approx(1 / 31)
    assert r.class_frequency[YearClass.DRY] == pytest.approx(10 / 31)


def test_tie_at_tercile_boundary() -> None:
    totals = {1990 + i: 100.0 + i for i in range(30)}
    totals[2003] = 500.0
    totals[2011] = 500.0
    # Forzar que 2003 y 2011 ocupen las posiciones 10 y 11 (índices 9 y 10).
    for y in totals:
        if y not in (2003, 2011):
            totals[y] = 400.0 + (y - 1990) if y < 2003 else 600.0 + (y - 1990)
    low = sorted(totals, key=lambda y: (round(totals[y], 1), y))
    lows = [y for y in low if totals[y] < 500]
    for y in lows[9:]:
        totals[y] = 600.0 + y - 1990
    r = classify_totals(totals, "WINTER", 15, ("x",))
    cls = {y.campaign_year: y.year_class for y in r.years}
    assert cls[2003] is YearClass.DRY and cls[2011] is YearClass.NORMAL
    assert r.tie_breaks and r.tie_breaks[0].years == (2003, 2011)


def test_float_noise() -> None:
    totals = {1990 + i: 100.0 + 10 * i for i in range(30)}
    totals[2001] = 412.04999999
    totals[2000] = 412.05
    r = classify_totals(totals, "WINTER", 15, ("x",))
    rains = {y.campaign_year: y.rain.value for y in r.years}
    assert rains[2000] == rains[2001] == 412.1


def test_insufficient_years() -> None:
    with pytest.raises(ClimateClassificationError) as err:
        classify_totals(_totals(12), "WINTER", 15, ("x",))
    assert err.value.code is ClimateErrorCode.INSUFFICIENT_YEARS
    assert "12" in str(err.value) and "15" in str(err.value)


def test_traceable_result() -> None:
    s = series(date(1981, 1, 1), date(2025, 12, 31))
    r = classify_window(s, SUMMER, CFG)
    years = [y.campaign_year for y in r.years]
    assert years == sorted(years)
    assert r.lower_bound.provenance.kind == "DERIVED"
    assert set(r.assumption_ids) >= {"A-CLI-01", "A-CLI-02", "A-CLI-03"}
    assert all(y.rain.provenance.derived_from == ("NASA_POWER:PRECTOTCORR",) for y in r.years)


def test_combined_three_classes_and_weights() -> None:
    s = series(date(1981, 1, 1), date(2025, 12, 31))
    c = build_scenarios(s, CFG)
    n = len(c.scenarios)
    assert n == 44  # 1981..2024 completas en ambas ventanas
    assert sum(sc.weight for sc in c.scenarios) == pytest.approx(1.0, abs=1e-9)
    dry = sum(1 for sc in c.scenarios if sc.annual_class is YearClass.DRY)
    assert dry == n // 3


def test_year_valid_in_one_window_only() -> None:
    gaps = {date(1995, 6, 1)}
    s = series(date(1981, 1, 1), date(2025, 12, 31), gaps=gaps)
    c = build_scenarios(s, CFG)
    assert 1995 not in {sc.campaign_start_year for sc in c.scenarios}
    assert any(e.campaign_year == 1995 for e in c.exclusions)


def test_independent_classes() -> None:
    # Inviernos secos crecientes y veranos húmedos decrecientes: las clases difieren.
    def mm(d: date) -> float:
        if 5 <= d.month <= 10:
            return 0.1 * (d.year - 1980)
        return 10.0 - 0.1 * (d.year - 1980)

    s = series(date(1981, 1, 1), date(2025, 12, 31), mm_fn=mm)
    c = build_scenarios(s, CFG)
    first = c.scenarios[0]
    assert first.winter_class is YearClass.DRY and first.summer_class is YearClass.WET


@settings(max_examples=15, deadline=None)
@given(st.integers(min_value=0, max_value=2**32))
def test_permutation_invariant(seed: int) -> None:
    import random

    s = series(date(1981, 1, 1), date(2000, 12, 31))
    days = list(s.days)
    random.Random(seed).shuffle(days)
    shuffled = s.model_copy(update={"days": tuple(days)})
    assert canonical_json(build_scenarios(s, CFG_SHORT)) == canonical_json(
        build_scenarios(shuffled, CFG_SHORT)
    )


def test_deterministic_snapshot_shape() -> None:
    s = series(date(1981, 1, 1), date(2025, 12, 31))
    a = canonical_json(build_scenarios(s, CFG))
    b = canonical_json(build_scenarios(s, CFG))
    assert a == b
    assert json.loads(a)["scenarios"][0]["campaign_start_year"] == 1981
