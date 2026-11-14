"""Constructores de objetos de dominio válidos para tests (valores de ejemplo, no reales)."""

from __future__ import annotations

from datetime import date
from typing import Any

from rastrojo.domain import (
    ActorProfile,
    AssumptionProvenance,
    BareSoilCalendar,
    Campaign,
    ClimateScenario,
    Constraints,
    Crop,
    CropEconomics,
    Dataset,
    DatedPValue,
    DerivedProvenance,
    EconomicParameters,
    EngineInput,
    GeoPoint,
    HarvestCostMode,
    LossYears,
    MarginRange,
    ObservedProvenance,
    Period,
    Plot,
    PriceBasis,
    PValue,
    ResolvedAssumption,
    Rotation,
    RotationResult,
    ScenarioWeather,
    ScoreBreakdown,
    Soil,
    Source,
    UserInputProvenance,
    WaterFeasibility,
    WaterInputs,
    WeatherSources,
    YearClass,
)

USER = UserInputProvenance()
DERIVED = DerivedProvenance(method="test", derived_from=("NASA_POWER:PRECTOTCORR",))


def power_source(variable: str = "PRECTOTCORR") -> Source:
    return Source(
        dataset=Dataset.NASA_POWER,
        variable=variable,
        period=Period(start=date(1981, 1, 1), end=date(2025, 12, 31)),
        spatial_resolution="0.5° x 0.625°",
        temporal_resolution="diaria",
        is_modeled=True,
    )


def pv(value: float, unit: str, prov: Any = USER) -> PValue:
    return PValue(value=value, unit=unit, provenance=prov)  # type: ignore[arg-type]


def assumption(aid: str) -> AssumptionProvenance:
    return AssumptionProvenance(assumption_id=aid)


def plot(**over: Any) -> Plot:
    data: dict[str, Any] = {
        "plot_id": "demo-casilda",
        "name": "Lote demo",
        "location": GeoPoint(lat=-33.07, lon=-61.12),
        "area_ha": pv(100, "ha", assumption("A-DEMO-01")),
    }
    data.update(over)
    return Plot(**data)


def rotation(rid: str = "R_MAIZE_SOY", campaigns: tuple[Campaign, ...] | None = None) -> Rotation:
    return Rotation(
        rotation_id=rid,
        name=rid,
        campaigns=campaigns or (Campaign(summer=Crop.MAIZE_EARLY), Campaign(summer=Crop.SOY_1ST)),
    )


def profile(**over: Any) -> ActorProfile:
    data: dict[str, Any] = {
        "profile_id": "OWNER",
        "label": "Propietario",
        "horizon_years": pv(10, "year", assumption("A-ACT-01")),
        "soil_weight_alpha": pv(5, "USD/ha/point", assumption("A-ACT-01")),
        "risk_aversion_lambda": pv(0.5, "ratio", assumption("A-ACT-01")),
        "discount_rate": pv(0.08, "fraction", assumption("A-ACT-01")),
        "constraints": Constraints(allow_double_crop=True, allow_cover_crop=True),
    }
    data.update(over)
    return ActorProfile(**data)


def dated(value: float, unit: str, aid: str = "A-DEMO-02") -> DatedPValue:
    return DatedPValue(
        value=value,
        unit=unit,
        provenance=assumption(aid),
        reference_date=date(2026, 11, 1),  # type: ignore[arg-type]
    )


def crop_economics(crop: Crop = Crop.SOY_1ST, **over: Any) -> CropEconomics:
    data: dict[str, Any] = {
        "crop": crop,
        "price": dated(300, "USD/t"),
        "price_basis": PriceBasis.FOB,
        "export_tax": dated(0.26, "fraction"),
        "direct_costs": dated(350, "USD/ha"),
        "harvest_cost_mode": HarvestCostMode.FRACTION_OF_REVENUE,
        "harvest_cost": dated(0.07, "fraction"),
        "marketing_cost": dated(0.03, "fraction"),
        "freight": dated(20, "USD/t"),
        "yields": {
            YearClass.DRY: dated(2.5, "t/ha"),
            YearClass.NORMAL: dated(3.5, "t/ha"),
            YearClass.WET: dated(4.0, "t/ha"),
        },
    }
    data.update(over)
    return CropEconomics(**data)


def scenario(year: int, weight: float, cls: YearClass = YearClass.NORMAL) -> ClimateScenario:
    return ClimateScenario(
        campaign_start_year=year,
        annual_class=cls,
        winter_class=cls,
        summer_class=cls,
        winter_rain=pv(250, "mm", ObservedProvenance(source=power_source())),
        summer_rain=pv(500, "mm", ObservedProvenance(source=power_source())),
        weight=weight,
    )


def weather(year: int, days: int = 3) -> ScenarioWeather:
    return ScenarioWeather(
        campaign_start_year=year,
        start_date=date(year, 6, 1),
        rain_mm=(0.0,) * days,
        et0_mm=(3.0,) * days,
        t2m_min_c=(5.0,) * days,
        t2m_max_c=(18.0,) * days,
        sources=WeatherSources(
            rain=power_source(),
            et0=DerivedProvenance(method="FAO-56 Penman-Monteith", derived_from=("NASA_POWER",)),
            t2m_min=power_source("T2M_MIN"),
            t2m_max=power_source("T2M_MAX"),
        ),
    )


def engine_input(**over: Any) -> EngineInput:
    data: dict[str, Any] = {
        "plot": plot(),
        "soil": Soil(organic_matter_pct=pv(2.8, "%")),
        "current_rotation": rotation("R_SOY_MONO", (Campaign(summer=Crop.SOY_1ST),)),
        "candidates": (
            rotation("R_MAIZE_SOY"),
            rotation("R_SOY_MONO", (Campaign(summer=Crop.SOY_1ST),)),
        ),
        "profile": profile(),
        "economics": EconomicParameters(crops=(crop_economics(),)),
        "scenarios": (scenario(2008, 0.5, YearClass.DRY), scenario(2014, 0.5, YearClass.WET)),
        "resolved_assumptions": {"A-WAT-01": ResolvedAssumption(value={"SOY_1ST": 1.15})},
        "water_inputs": WaterInputs(weather=(weather(2008), weather(2014))),
    }
    data.update(over)
    return EngineInput(**data)


def breakdown(npv: float, soil: float, risk: float) -> ScoreBreakdown:
    return ScoreBreakdown(
        npv=pv(npv, "USD/ha", DERIVED),
        soil_term=pv(soil, "USD/ha", DERIVED),
        risk_term=pv(risk, "USD/ha", DERIVED),
        total=pv(npv + soil - risk, "USD/ha", DERIVED),
    )


def result(
    rid: str, rank: int, total: float, current_total: float, is_current: bool = False, **over: Any
) -> RotationResult:
    data: dict[str, Any] = {
        "rotation_id": rid,
        "rank": rank,
        "is_current": is_current,
        "eligible": True,
        "breakdown": breakdown(total, 0, 0),
        "soil_delta_index": pv(10, "index", DERIVED),
        "water_feasibility": WaterFeasibility.FEASIBLE,
        "score_delta_vs_current": pv(0 if is_current else total - current_total, "USD/ha", DERIVED),
        "margin_ranges": tuple(
            MarginRange(
                year_class=c,
                minimum=pv(100, "USD/ha", DERIVED),
                expected=pv(200, "USD/ha", DERIVED),
                maximum=pv(300, "USD/ha", DERIVED),
            )
            for c in YearClass
        ),
        "loss_years": LossYears(count=1, total=45, years=(2008,)),
        "worst_year_margin": pv(-50, "USD/ha", DERIVED),
        "worst_year": 2008,
        "rain_on_bare_soil": pv(120, "mm", DERIVED),
        "bare_soil_calendar": BareSoilCalendar(days_by_month=(0.0,) * 12, provenance=DERIVED),
        "vulnerability_calendar": (),
        "evidence": (),
        "benefits": (),
        "missing": (),
        "risks": (),
    }
    data.update(over)
    return RotationResult(**data)
