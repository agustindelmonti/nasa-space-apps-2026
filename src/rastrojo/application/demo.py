"""Armado del `EngineInput` del lote demo desde datos reales de NASA POWER y el registro de supuestos.

Este módulo sí hace I/O (lee caché y registro); el motor que lo consume es puro.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache

import pandas as pd

from rastrojo.application.assumptions import AssumptionRegistry, climate_config, resolve
from rastrojo.data.power import PowerDaily, get_power_daily
from rastrojo.domain import (
    ActorProfile,
    AssumptionProvenance,
    Campaign,
    ClimateScenario,
    Constraints,
    Crop,
    CropEconomics,
    DatedPValue,
    EconomicParameters,
    EngineInput,
    GeoPoint,
    HarvestCostMode,
    Plot,
    PriceBasis,
    PValue,
    Rotation,
    ScenarioWeather,
    ServiceCropCosts,
    Soil,
    TextureClass,
    TextureValue,
    WaterInputs,
    WeatherSources,
    YearClass,
    YearClassFilter,
)
from rastrojo.domain.actor import MachineryWindows, SoilPriorities
from rastrojo.domain.crops import CROP_INFO, CropKind
from rastrojo.domain.provenance import Dataset
from rastrojo.engine.climate import RainDay, RainSeries, build_scenarios
from rastrojo.engine.economics import ECONOMICS_ASSUMPTIONS
from rastrojo.engine.soil import SOIL_ASSUMPTIONS
from rastrojo.engine.water import WATER_ASSUMPTIONS

DEMO_PLOT_ID = "demo-casilda"
POWER_START = date(1981, 1, 1)
POWER_END = date(2025, 12, 31)
WEATHER_DAYS = 426  # 1/5 del año de campaña al 30/6 del año siguiente
PARAM_DATE = date(2026, 11, 1)

CATALOG: tuple[Rotation, ...] = (
    Rotation(
        rotation_id="R_SOY_MONO", name="Soja continua", campaigns=(Campaign(summer=Crop.SOY_1ST),)
    ),
    Rotation(
        rotation_id="R_MAIZE_SOY",
        name="Maíz / Soja",
        campaigns=(Campaign(summer=Crop.MAIZE_EARLY), Campaign(summer=Crop.SOY_1ST)),
    ),
    Rotation(
        rotation_id="R_WHEAT_SOY2_MAIZE",
        name="Trigo / Soja 2ª → Maíz",
        campaigns=(
            Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND),
            Campaign(summer=Crop.MAIZE_EARLY),
        ),
    ),
    Rotation(
        rotation_id="R_MAIZE_SOY_COVER",
        name="Maíz / Soja con centeno de servicio",
        campaigns=(
            Campaign(summer=Crop.MAIZE_EARLY),
            Campaign(winter=Crop.COVER_RYE, summer=Crop.SOY_1ST),
        ),
    ),
    Rotation(
        rotation_id="R_SOY_COVER",
        name="Soja con vicia de servicio",
        campaigns=(Campaign(winter=Crop.COVER_VETCH, summer=Crop.SOY_1ST),),
    ),
)
CATALOG_BY_ID = {r.rotation_id: r for r in CATALOG}

PROFILE_ASSUMPTIONS = {
    "OWNER": "A-ACT-01",
    "TENANT": "A-ACT-02",
    "COOP": "A-ACT-03",
    "BANK": "A-ACT-04",
}
ENGINE_ASSUMPTIONS = tuple(
    sorted(
        set(WATER_ASSUMPTIONS)
        | set(SOIL_ASSUMPTIONS)
        | set(ECONOMICS_ASSUMPTIONS)
        | {"A-ACT-05", "A-ACT-07", "A-CLI-02", "A-CLI-03", "A-CLI-07"}
    )
)


def _assume(aid: str) -> AssumptionProvenance:
    return AssumptionProvenance(assumption_id=aid)


def _pv(value: float, unit: str, aid: str) -> PValue:
    return PValue(value=value, unit=unit, provenance=_assume(aid))


def _dated(value: float, unit: str, aid: str) -> DatedPValue:
    return DatedPValue(value=value, unit=unit, provenance=_assume(aid), reference_date=PARAM_DATE)


def actor_profile(
    registry: AssumptionRegistry,
    profile_id: str,
    *,
    horizon_years: int | None = None,
    alpha: float | None = None,
    risk_aversion: float | None = None,
    discount_rate: float | None = None,
    priorities: SoilPriorities | None = None,
    machinery_windows: MachineryWindows | None = None,
) -> ActorProfile:
    """Perfil predefinido (A-ACT-01..04) con overrides opcionales del usuario (sliders)."""
    aid = PROFILE_ASSUMPTIONS[profile_id]
    v = dict(registry.value(aid))
    limits = dict(registry.value("A-ACT-06"))

    def field(name: str, override: float | None, unit: str, limit_key: str) -> PValue:
        if override is None:
            return _pv(float(v[name]), unit, aid)
        lo, hi = limits[limit_key]
        if not (float(lo) <= override <= float(hi)):
            raise ValueError(f"{limit_key} fuera de rango ({lo} a {hi}) según A-ACT-06")
        return PValue(value=float(override), unit=unit, provenance={"kind": "USER_INPUT"})

    cap = v.get("max_working_capital_usd_ha")
    return ActorProfile(
        profile_id=profile_id,
        label=str(v["label"]),
        horizon_years=field("horizon_years", horizon_years, "year", "horizon_years"),
        soil_weight_alpha=field("alpha", alpha, "USD/ha/point", "alpha"),
        risk_aversion_lambda=field("lambda", risk_aversion, "ratio", "lambda"),
        discount_rate=field("discount_rate", discount_rate, "fraction", "discount_rate"),
        constraints=Constraints(
            allow_double_crop=bool(v["allow_double_crop"]),
            allow_cover_crop=bool(v["allow_cover_crop"]),
            max_working_capital_usd_ha=_pv(float(cap), "USD/ha", aid) if cap is not None else None,
        ),
        priorities=priorities,
        machinery_windows=machinery_windows,
    )


def demo_economics(registry: AssumptionRegistry) -> EconomicParameters:
    prices = dict(registry.value("A-DEMO-02"))
    taxes = dict(registry.value("A-DEMO-03"))
    costs = dict(registry.value("A-DEMO-04"))
    other = dict(registry.value("A-DEMO-05"))
    yields = dict(registry.value("A-DEMO-06"))
    cash: list[CropEconomics] = []
    services: list[ServiceCropCosts] = []
    for crop in Crop:
        if CROP_INFO[crop].kind is CropKind.SERVICE:
            services.append(
                ServiceCropCosts(
                    crop=crop, direct_costs=_dated(float(costs[crop.value]), "USD/ha", "A-DEMO-04")
                )
            )
            continue
        price, basis = prices[crop.value]
        y = yields[crop.value]
        cash.append(
            CropEconomics(
                crop=crop,
                price=_dated(float(price), "USD/t", "A-DEMO-02"),
                price_basis=PriceBasis(basis),
                export_tax=_dated(float(taxes[crop.value]), "fraction", "A-DEMO-03"),
                direct_costs=_dated(float(costs[crop.value]), "USD/ha", "A-DEMO-04"),
                harvest_cost_mode=HarvestCostMode.FRACTION_OF_REVENUE,
                harvest_cost=_dated(float(other["harvest_fraction"]), "fraction", "A-DEMO-05"),
                marketing_cost=_dated(float(other["marketing_fraction"]), "fraction", "A-DEMO-05"),
                freight=_dated(float(other["freight_usd_t"]), "USD/t", "A-DEMO-05"),
                yields={
                    YearClass.DRY: _dated(float(y[0]), "t/ha", "A-DEMO-06"),
                    YearClass.NORMAL: _dated(float(y[1]), "t/ha", "A-DEMO-06"),
                    YearClass.WET: _dated(float(y[2]), "t/ha", "A-DEMO-06"),
                },
            )
        )
    return EconomicParameters(crops=tuple(cash), service_crops=tuple(services))


def demo_plot(registry: AssumptionRegistry) -> Plot:
    v = dict(registry.value("A-DEMO-01"))
    return Plot(
        plot_id=DEMO_PLOT_ID,
        name="Lote de ejemplo, Casilda",
        location=GeoPoint(lat=float(v["lat"]), lon=float(v["lon"])),
        area_ha=_pv(float(v["area_ha"]), "ha", "A-DEMO-01"),
    )


def demo_soil(registry: AssumptionRegistry) -> Soil:
    v = dict(registry.value("A-DEMO-07"))
    return Soil(
        texture=TextureValue(value=TextureClass(v["texture"]), provenance=_assume("A-DEMO-07")),
        organic_matter_pct=_pv(float(v["organic_matter_pct"]), "%", "A-DEMO-07"),
    )


@dataclass(frozen=True)
class ClimateBundle:
    scenarios: tuple[ClimateScenario, ...]
    weather: tuple[ScenarioWeather, ...]
    excluded_years: tuple[int, ...]


def _rain_series(power: PowerDaily, wide: pd.DataFrame) -> RainSeries:
    src = power.source("PRECTOTCORR")
    days = tuple(
        RainDay(
            day=pd.Timestamp(str(d)).date(),
            mm=None if pd.isna(v) else float(v),
            dataset=Dataset.NASA_POWER,
        )
        for d, v in wide["PRECTOTCORR"].items()
    )
    return RainSeries(source=src, days=days)


def build_climate(power: PowerDaily, registry: AssumptionRegistry) -> ClimateBundle:
    wide = power.wide()
    et0 = power.et0().set_index("date")["value"]
    combined = build_scenarios(_rain_series(power, wide), climate_config(registry))
    sources = WeatherSources(
        rain=power.source("PRECTOTCORR"),
        et0=power.et0_provenance,
        t2m_min=power.source("T2M_MIN"),
        t2m_max=power.source("T2M_MAX"),
    )
    weather: list[ScenarioWeather] = []
    excluded: list[int] = []
    for sc in combined.scenarios:
        start = date(sc.campaign_start_year, 5, 1)
        idx = [pd.Timestamp(start + timedelta(days=k)) for k in range(WEATHER_DAYS)]
        try:
            rain = wide.loc[idx, "PRECTOTCORR"]
            tmin = wide.loc[idx, "T2M_MIN"]
            tmax = wide.loc[idx, "T2M_MAX"]
            e = et0.loc[idx]
        except KeyError:
            excluded.append(sc.campaign_start_year)
            continue
        if rain.isna().any() or tmin.isna().any() or tmax.isna().any() or e.isna().any():
            excluded.append(sc.campaign_start_year)
            continue
        weather.append(
            ScenarioWeather(
                campaign_start_year=sc.campaign_start_year,
                start_date=start,
                rain_mm=tuple(round(float(x), 3) for x in rain),
                et0_mm=tuple(round(float(x), 3) for x in e),
                t2m_min_c=tuple(round(float(x), 2) for x in tmin),
                t2m_max_c=tuple(round(float(x), 2) for x in tmax),
                sources=sources,
            )
        )
    kept = {w.campaign_start_year for w in weather}
    selected = [s for s in combined.scenarios if s.campaign_start_year in kept]
    total = math.fsum(s.weight for s in selected)
    scenarios = tuple(s.model_copy(update={"weight": s.weight / total}) for s in selected)
    return ClimateBundle(
        scenarios=scenarios, weather=tuple(weather), excluded_years=tuple(excluded)
    )


@lru_cache(maxsize=4)
def _demo_climate(lat: float, lon: float) -> ClimateBundle:
    registry = AssumptionRegistry.load()
    power = get_power_daily(lat, lon, POWER_START, POWER_END)
    return build_climate(power, registry)


def build_engine_input(
    profile: ActorProfile,
    current_rotation_id: str = "R_SOY_MONO",
    current_rotation: Rotation | None = None,
    year_class_filter: YearClassFilter = YearClassFilter.ALL,
    registry: AssumptionRegistry | None = None,
) -> EngineInput:
    registry = registry or AssumptionRegistry.load()
    plot = demo_plot(registry)
    climate = _demo_climate(plot.location.lat, plot.location.lon)
    current = current_rotation or CATALOG_BY_ID[current_rotation_id]
    return EngineInput(
        plot=plot,
        soil=demo_soil(registry),
        current_rotation=current,
        candidates=CATALOG,
        profile=profile,
        economics=demo_economics(registry),
        scenarios=climate.scenarios,
        resolved_assumptions=resolve(registry, ENGINE_ASSUMPTIONS),
        water_inputs=WaterInputs(weather=climate.weather),
        year_class_filter=year_class_filter,
    )
