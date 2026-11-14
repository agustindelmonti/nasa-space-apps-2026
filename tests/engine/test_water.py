from __future__ import annotations

import subprocess
import sys

import pytest

from rastrojo.domain import (
    Campaign,
    Crop,
    Rotation,
    Soil,
    TextureClass,
    TextureValue,
    WaterFeasibility,
)
from rastrojo.domain.provenance import (
    Dataset,
    DerivedProvenance,
    ObservedProvenance,
    Period,
    Source,
)
from rastrojo.engine.water import (
    ReasonCode,
    bucket_step,
    campaign_windows,
    evaluate_rotation,
    kc_for_day,
    resolve_awc,
    resolve_initial,
    water_config,
    worst,
)
from tests.domain.factories import USER, pv
from tests.engine.water_fixtures import inputs, resolved, scenarios_and_weather, weather_year

SOIL = Soil(
    available_water_mm=pv(150, "mm"),
    texture=TextureValue(value=TextureClass.SILT_LOAM, provenance=USER),
)
WHEAT_SOY2 = Rotation(
    rotation_id="R_WHEAT_SOY2",
    name="t/s2",
    campaigns=(Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND),),
)
RYE_SOY = Rotation(
    rotation_id="R_SOY_COVER",
    name="c/s",
    campaigns=(Campaign(winter=Crop.COVER_RYE, summer=Crop.SOY_1ST),),
)
SOY = Rotation(rotation_id="R_SOY_MONO", name="s", campaigns=(Campaign(summer=Crop.SOY_1ST),))


def cfg():
    return water_config(resolved())


# Balance diario
def test_excess_drained() -> None:
    r = bucket_step(prev=140, eff_rain=30, etc=4, awc=150, p=0.5)
    assert r.water == 150 and r.drainage == pytest.approx(16)


def test_no_stress_full_profile() -> None:
    r = bucket_step(prev=150, eff_rain=0, etc=5, awc=150, p=0.5)
    assert r.ks == 1.0 and r.eta == 5


def test_empty_profile() -> None:
    r = bucket_step(prev=0, eff_rain=0, etc=5, awc=150, p=0.5)
    assert r.ks == 0 and r.eta == 0


def test_effective_rain_fraction() -> None:
    assert cfg().rain_fraction * 20 == pytest.approx(16)


def test_kc_curve() -> None:
    kc = (0.4, 1.15, 0.5)
    fr = cfg().stage_fractions
    assert kc_for_day(kc, fr, 0.0) == 0.4
    assert kc_for_day(kc, fr, 0.5) == 1.15
    assert kc_for_day(kc, fr, 1.0) == pytest.approx(0.5)


def test_fallow_between_crops() -> None:
    w = campaign_windows(WHEAT_SOY2.campaigns[0], 2008, cfg())
    assert w[0].end < w[1].start  # días entre cosecha de trigo y siembra de soja = barbecho


def test_cover_termination() -> None:
    c = cfg()
    w = campaign_windows(RYE_SOY.campaigns[0], 2008, c)
    assert (w[1].start - w[0].end).days == c.cover_termination_days


# Suelo e inicio
def test_smap_conversion() -> None:
    src = Source(
        dataset=Dataset.SMAP_L4,
        variable="sm_rootzone",
        period=Period(start="2026-11-01", end="2026-11-01"),
        spatial_resolution="~9 km",
        temporal_resolution="3-horaria",
        is_modeled=True,
    )
    smap = pv(0.30, "m3/m3", ObservedProvenance(source=src))
    c = cfg()
    c.theta["SILT_LOAM"] = (0.35, 0.15)  # valores del escenario de la spec
    init, reasons, _ = resolve_initial(
        SOIL, inputs((weather_year(2008),), smap=smap), SOIL.available_water_mm, c
    )
    assert init.value == pytest.approx(112.5)
    assert "SMAP_L4:sm_rootzone" in init.provenance.derived_from and not reasons


def test_without_smap() -> None:
    init, reasons, missing = resolve_initial(
        SOIL, inputs((weather_year(2008),)), SOIL.available_water_mm, cfg()
    )
    assert reasons[0].code is ReasonCode.INITIAL_MOISTURE_ASSUMED and missing
    assert init.value == pytest.approx(75)


def test_soil_without_awc() -> None:
    soil = Soil(texture=TextureValue(value=TextureClass.SILT_LOAM, provenance=USER))
    awc, reasons, missing = resolve_awc(soil, cfg())
    assert reasons[0].code is ReasonCode.SOIL_AWC_ASSUMED
    assert any(m.item == "agua útil del perfil" for m in missing)
    assert awc.value == pytest.approx((0.29 - 0.15) * 1.4 * 1000)


def test_awc_from_soilgrids() -> None:
    soil = Soil(
        available_water_mm=pv(
            170,
            "mm",
            DerivedProvenance(
                method="suma por capa", derived_from=("SOILGRIDS:wv0033", "A-WAT-17")
            ),
        )
    )
    _, reasons, missing = resolve_awc(soil, cfg())
    assert reasons[0].code is ReasonCode.SOIL_AWC_FROM_SOILGRIDS
    assert "250 m" in missing[0].why_it_matters


# Escenarios y estado
def test_result_by_year() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())
    rows = a.campaigns[0].scenarios
    assert len(rows) == 30
    r = rows[0]
    assert {c.crop for c in r.crops} == {Crop.WHEAT, Crop.SOY_2ND}
    assert r.water_at_summer_sowing is not None


def test_year_without_complete_weather() -> None:
    scen, wx = scenarios_and_weather(30)
    wx = tuple(weather_year(1992, days=100) if w.campaign_start_year == 1992 else w for w in wx)
    a = evaluate_rotation(SOY, SOIL, scen, inputs(wx), resolved())
    camp = a.campaigns[0]
    assert camp.valid_scenarios == 29
    codes = {r.code for r in camp.reasons}
    assert ReasonCode.MISSING_WEATHER in codes and ReasonCode.SCENARIOS_EXCLUDED in codes
    st = [s for s in a.crop_status if s.campaign_start_year == 1992]
    assert st and all(s.status is WaterFeasibility.UNKNOWN for s in st)


def test_insufficient_scenarios_unknown_not_infeasible() -> None:
    scen, wx = scenarios_and_weather(10)
    scen = tuple(s.model_copy(update={"weight": 0.1}) for s in scen)
    a = evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())
    assert a.status is WaterFeasibility.UNKNOWN
    assert ReasonCode.INSUFFICIENT_SCENARIOS in {r.code for r in a.campaigns[0].reasons}
    assert any("10 años válidos" in m.why_it_matters for m in a.missing)


def test_complete_data_no_unknown() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(SOY, SOIL, scen, inputs(wx), resolved())
    assert a.status is not WaterFeasibility.UNKNOWN
    assert all(s.status is not WaterFeasibility.UNKNOWN for s in a.crop_status)


def test_dry_climate_makes_double_crop_worse() -> None:
    dry = {y: 0.25 for y in range(1990, 2020)}
    scen, wx = scenarios_and_weather(30, scales=dry)
    a = evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())
    assert a.status in (WaterFeasibility.RISKY, WaterFeasibility.NOT_FEASIBLE)
    assert any(r.code is ReasonCode.SEVERE_STRESS_FREQUENT for r in a.campaigns[0].reasons)


def test_worst_order() -> None:
    assert (
        worst([WaterFeasibility.FEASIBLE, WaterFeasibility.NOT_FEASIBLE])
        is WaterFeasibility.NOT_FEASIBLE
    )
    assert worst([WaterFeasibility.RISKY, WaterFeasibility.UNKNOWN]) is WaterFeasibility.UNKNOWN


def test_cover_crop_water_cost() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(RYE_SOY, SOIL, scen, inputs(wx), resolved())
    camp = a.campaigns[0]
    assert camp.cover_water_cost is not None and camp.cover_water_cost.provenance.kind == "DERIVED"
    assert camp.scenarios[0].fallow_water_at_summer_sowing is not None


def test_grace_only_escalates_feasible() -> None:
    wet = {y: 1.6 for y in range(1990, 2020)}
    scen, wx = scenarios_and_weather(30, scales=wet)
    base = evaluate_rotation(SOY, SOIL, scen, inputs(wx), resolved())
    assert base.status is WaterFeasibility.FEASIBLE
    tws_src = Source(
        dataset=Dataset.GRACE_FO,
        variable="lwe_thickness",
        period=Period(start="2026-07-01", end="2026-09-30"),
        spatial_resolution="~300 km",
        temporal_resolution="mensual",
        is_modeled=True,
    )
    a = evaluate_rotation(
        SOY,
        SOIL,
        scen,
        inputs(wx, tws=pv(-80, "mm", ObservedProvenance(source=tws_src))),
        resolved(),
    )
    assert a.status is WaterFeasibility.RISKY
    assert ReasonCode.GRACE_REGIONAL_DEFICIT in {r.code for r in a.campaigns[0].reasons}
    assert any("300 km" in e.interpretation for e in a.evidence)


def test_water_table_missing_and_mitigates() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(SOY, SOIL, scen, inputs(wx), resolved())
    assert any(m.item == "profundidad de napa" for m in a.missing)
    soil = SOIL.model_copy(update={"water_table_depth_m": pv(2.0, "m")})
    b = evaluate_rotation(SOY, soil, scen, inputs(wx), resolved())
    assert ReasonCode.SHALLOW_WATER_TABLE_MITIGATES in {r.code for r in b.reasons}
    assert a.status is b.status


def test_frost_risk_does_not_change_status() -> None:
    scen, wx = scenarios_and_weather(30, tmin_offset=-12)
    a = evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())
    scen2, wx2 = scenarios_and_weather(30)
    b = evaluate_rotation(WHEAT_SOY2, SOIL, scen2, inputs(wx2), resolved())
    assert any(r.risk_type.value == "FROST" for r in a.risks)
    assert a.status is b.status


def test_vulnerability_calendar() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())
    wheat_def = next(
        v for v in a.vulnerability if v.crop is Crop.WHEAT and v.event == "WATER_DEFICIT"
    )
    assert wheat_def.in_field_by_month[0] is False  # enero: el trigo ya está cosechado
    assert len(wheat_def.frequency_by_month) == 12
    assert not any(v.event == "EXTREME_RAIN" for v in a.vulnerability)  # sin IMERG
    assert any(m.item == "lluvia diaria IMERG" for m in a.missing)


def test_heat_stress_calendar() -> None:
    maize = Rotation(
        rotation_id="R_MAIZE", name="m", campaigns=(Campaign(summer=Crop.MAIZE_EARLY),)
    )
    scen, wx = scenarios_and_weather(30, tmax_offset=6)
    a = evaluate_rotation(maize, SOIL, scen, inputs(wx), resolved())
    heat = next(v for v in a.vulnerability if v.event == "HEAT_STRESS")
    assert max(heat.frequency_by_month) > 0


def test_conservative_rain_imerg() -> None:
    scen, wx = scenarios_and_weather(30, imerg_scale=0.7)
    a = evaluate_rotation(SOY, SOIL, scen, inputs(wx), resolved())
    assert all(s.rain_source is Dataset.GPM_IMERG for s in a.campaigns[0].scenarios)
    assert ReasonCode.CONSERVATIVE_RAIN_SOURCE in {r.code for r in a.campaigns[0].reasons}
    assert any(v.event == "EXTREME_RAIN" for v in a.vulnerability)


def test_class_ranges() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())
    ranges = {r.year_class.value: r for r in a.campaigns[0].ranges}
    assert set(ranges) == {"DRY", "NORMAL", "WET"}
    dry = ranges["DRY"]
    assert dry.sowing_water_min.value <= dry.sowing_water_mean.value <= dry.sowing_water_max.value


def test_assumptions_listed() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_rotation(SOY, SOIL, scen, inputs(wx), resolved())
    assert {"A-WAT-01", "A-WAT-02", "A-WAT-03", "A-WAT-05", "A-WAT-06", "A-WAT-07"} <= set(
        a.assumptions_used
    )
    assert any(e.dataset is Dataset.NASA_POWER for e in a.evidence)


def test_deterministic_two_processes() -> None:
    code = (
        "from rastrojo.domain import canonical_json\nfrom tests.engine.test_water import *\n"
        "scen, wx = scenarios_and_weather(30)\n"
        "import sys; sys.stdout.buffer.write(canonical_json(evaluate_rotation(WHEAT_SOY2, SOIL, scen, inputs(wx), resolved())))"
    )
    outs = [
        subprocess.run([sys.executable, "-c", code], capture_output=True, check=True).stdout
        for _ in range(2)
    ]
    assert outs[0] == outs[1] and len(outs[0]) > 1000
