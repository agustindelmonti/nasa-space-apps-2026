"""Humedad inicial desde GWETROOT (NASA POWER) y castigo de rinde solo con estrés severo."""

from __future__ import annotations

from functools import cache

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import actor_profile, build_engine_input
from rastrojo.domain.results import WaterFeasibility
from rastrojo.engine.rotation import evaluate


@cache
def _inp():
    reg = AssumptionRegistry.load()
    return build_engine_input(actor_profile(reg, "OWNER"), registry=reg)


@cache
def _out():
    return evaluate(_inp())


def test_demo_weather_carries_gwetroot_with_its_source() -> None:
    weather = _inp().water_inputs.weather
    assert all(w.gwetroot is not None for w in weather)
    src = weather[0].sources.gwetroot
    assert src is not None and src.variable == "GWETROOT" and src.dataset.value == "NASA_POWER"


def test_initial_moisture_is_no_longer_an_assumption() -> None:
    for r in _out().results:
        assert "INITIAL_MOISTURE_ASSUMED" not in r.water_reasons
        assert any(e.variable.startswith("GWETROOT") for e in r.evidence)


def test_moderate_stress_does_not_cut_the_yield_twice() -> None:
    for r in _out().results:
        for a in r.water_adjustments:
            assert a.effect == "FORCE_DRY"
            assert a.status in (WaterFeasibility.NOT_FEASIBLE, WaterFeasibility.RISKY)


def test_soy_mono_margin_is_close_to_its_unadjusted_value() -> None:
    soy = next(r for r in _out().results if r.rotation_id == "R_SOY_MONO")
    assert soy.expected_annual_margin is not None
    # 212 (seco), 389 (normal), 495 (húmedo) con los supuestos de ejemplo: ~365 sin agua.
    assert 300 <= soy.expected_annual_margin.value <= 400


def test_imerg_series_reaches_the_water_balance() -> None:
    weather = _inp().water_inputs.weather
    with_imerg = [w for w in weather if w.imerg_rain_mm is not None]
    assert len(with_imerg) >= 25  # IMERG v07 cubre desde 1998
    assert with_imerg[0].sources.imerg_rain is not None
    assert all(w.sources.imerg_rain is None for w in weather if w.imerg_rain_mm is None)
    soy = next(r for r in _out().results if r.rotation_id == "R_SOY_MONO")
    assert "CONSERVATIVE_RAIN_SOURCE" in soy.water_reasons
