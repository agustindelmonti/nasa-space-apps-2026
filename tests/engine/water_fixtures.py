"""Clima sintético reproducible para tests del balance (no son datos reales)."""

from __future__ import annotations

import math
from datetime import date, timedelta

from rastrojo.application.assumptions import AssumptionRegistry, resolve
from rastrojo.domain import (
    ClimateScenario,
    DerivedProvenance,
    ScenarioWeather,
    WaterInputs,
    WeatherSources,
    YearClass,
)
from rastrojo.engine.water import WATER_ASSUMPTIONS
from tests.domain.factories import power_source, pv

DAYS = 426  # 1/5 del año Y al 30/6 del año Y+1


def resolved():
    return resolve(AssumptionRegistry.load(), WATER_ASSUMPTIONS)


def weather_year(
    year: int,
    rain_scale: float = 1.0,
    tmin_offset: float = 0.0,
    tmax_offset: float = 0.0,
    imerg_scale: float | None = None,
    days: int = DAYS,
) -> ScenarioWeather:
    start = date(year, 5, 1)
    rain, et0, tmin, tmax = [], [], [], []
    for i in range(days):
        d = start + timedelta(days=i)
        doy = d.timetuple().tm_yday
        season = math.cos(2 * math.pi * (doy - 15) / 365)  # 1 en enero (verano austral)
        et0.append(round(3.5 + 2.5 * season, 3))
        rain.append(round(rain_scale * (9.0 if i % 6 == 0 else 0.0) * (1.0 + 0.6 * season), 3))
        tmin.append(round(9 + 8 * season + tmin_offset, 2))
        tmax.append(round(22 + 9 * season + tmax_offset, 2))
    imerg = None
    if imerg_scale is not None:
        imerg = tuple(round(r * imerg_scale, 3) for r in rain)
    sources = WeatherSources(
        rain=power_source(),
        et0=DerivedProvenance(method="FAO-56 Penman-Monteith", derived_from=("NASA_POWER",)),
        t2m_min=power_source("T2M_MIN"),
        t2m_max=power_source("T2M_MAX"),
        imerg_rain=power_source("IMERG") if imerg is not None else None,
    )
    return ScenarioWeather(
        campaign_start_year=year,
        start_date=start,
        rain_mm=tuple(rain),
        et0_mm=tuple(et0),
        t2m_min_c=tuple(tmin),
        t2m_max_c=tuple(tmax),
        imerg_rain_mm=imerg,
        sources=sources,
    )


def scenarios_and_weather(n: int = 30, scales: dict[int, float] | None = None, **kw):
    years = list(range(1990, 1990 + n))
    scales = scales or {y: 0.6 + 0.9 * ((y * 7) % n) / n for y in years}
    ranked = sorted(years, key=lambda y: (scales[y], y))
    k = n // 3
    cls = {
        y: (YearClass.DRY if i < k else YearClass.WET if i >= n - k else YearClass.NORMAL)
        for i, y in enumerate(ranked)
    }
    scen = tuple(
        ClimateScenario(
            campaign_start_year=y,
            annual_class=cls[y],
            winter_class=cls[y],
            summer_class=cls[y],
            winter_rain=pv(200 * scales[y], "mm"),
            summer_rain=pv(500 * scales[y], "mm"),
            weight=1.0 / n,
        )
        for y in years
    )
    weather = tuple(weather_year(y, scales[y], **kw) for y in years)
    return scen, weather


def inputs(weather, smap=None, tws=None) -> WaterInputs:
    return WaterInputs(weather=weather, smap_initial_rootzone=smap, grace_tws_anomaly=tws)
