from __future__ import annotations

from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from rastrojo.application.assumptions import AssumptionRegistry, resolve
from rastrojo.domain import (
    Campaign,
    ClimateScenario,
    Crop,
    DatedPValue,
    EconomicParameters,
    PriceBasis,
    Rent,
    Rotation,
    ServiceCropCosts,
    YearClass,
)
from rastrojo.domain.provenance import UserInputProvenance
from rastrojo.engine.economics import (
    ECONOMICS_ASSUMPTIONS,
    MissingEconomicParameterError,
    annuity_factor,
    crop_margin,
    evaluate_economics,
    net_price,
    npv_by_phases,
)
from tests.domain.factories import crop_economics, dated, pv


def res():
    return resolve(AssumptionRegistry.load(), ECONOMICS_ASSUMPTIONS)


SOY = crop_economics(
    Crop.SOY_1ST,
    price=dated(300, "USD/t"),
    export_tax=dated(0.26, "fraction"),
    direct_costs=dated(250, "USD/ha"),
    harvest_cost=dated(0.08, "fraction"),
    marketing_cost=dated(0.03, "fraction"),
    freight=dated(20, "USD/t"),
)


def scen(year: int, cls=YearClass.NORMAL, winter=None, summer=None, weight=1.0):
    return ClimateScenario(
        campaign_start_year=year,
        annual_class=cls,
        winter_class=winter or cls,
        summer_class=summer or cls,
        winter_rain=pv(200, "mm"),
        summer_rain=pv(500, "mm"),
        weight=weight,
    )


def rot(rid, *camps):
    return Rotation(rotation_id=rid, name=rid, campaigns=camps)


def test_soy_margin_normal_year() -> None:
    assert net_price(SOY) * 3.5 == pytest.approx(777)
    assert crop_margin(SOY, YearClass.NORMAL) == pytest.approx(371.53)


def test_season_class() -> None:
    wheat = crop_economics(Crop.WHEAT)
    soy2 = crop_economics(Crop.SOY_2ND)
    params = EconomicParameters(crops=(wheat, soy2))
    r = rot("R_WS2", Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND))
    out = evaluate_economics(
        r, params, (scen(2008, winter=YearClass.DRY, summer=YearClass.WET),), 1, 0.0, res()
    )
    expected = crop_margin(wheat, YearClass.DRY) + crop_margin(soy2, YearClass.WET)
    assert out.margin_matrix[0].margin.value == pytest.approx(expected)


def test_rye_without_price() -> None:
    params = EconomicParameters(
        crops=(SOY,),
        service_crops=(ServiceCropCosts(crop=Crop.COVER_RYE, direct_costs=dated(90, "USD/ha")),),
    )
    r = rot("R_SOY_COVER", Campaign(winter=Crop.COVER_RYE, summer=Crop.SOY_1ST))
    out = evaluate_economics(r, params, (scen(2008),), 1, 0.0, res())
    assert out.margin_matrix[0].margin.value == pytest.approx(371.53 - 90)


def test_spot_price_not_taxed_twice() -> None:
    maize = crop_economics(
        Crop.MAIZE_EARLY, price_basis=PriceBasis.SPOT_FAS, export_tax=dated(0.12, "fraction")
    )
    assert net_price(maize) == maize.price.value


def test_not_sown_adjustment() -> None:
    wheat = crop_economics(Crop.WHEAT)
    params = EconomicParameters(crops=(wheat, crop_economics(Crop.SOY_2ND)))
    r = rot("R_WS2", Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND))
    out = evaluate_economics(
        r, params, (scen(2008),), 1, 0.0, res(), {(Crop.SOY_2ND, 0, 2008): "NOT_SOWN"}
    )
    assert out.margin_matrix[0].margin.value == pytest.approx(crop_margin(wheat, YearClass.NORMAL))
    assert out.adjustments[0].effect == "NOT_SOWN"


def test_rent_in_quintals() -> None:
    soy = SOY.model_copy(
        update={"price": dated(300, "USD/t"), "export_tax": dated(0.26, "fraction")}
    )
    params = EconomicParameters(crops=(soy,), rent=Rent(soy_qq_ha=dated(15, "qq/ha")))
    r = rot("R_SOY", Campaign(summer=Crop.SOY_1ST))
    out = evaluate_economics(r, params, (scen(2008),), 1, 0.0, res())
    assert out.margin_matrix[0].margin.value == pytest.approx(371.53 - 15 * 0.1 * 222)
    assert out.lease_included


def test_without_rent() -> None:
    out = evaluate_economics(
        rot("R_SOY", Campaign(summer=Crop.SOY_1ST)),
        EconomicParameters(crops=(SOY,)),
        (scen(2008),),
        1,
        0.0,
        res(),
    )
    assert out.lease_included is False


def test_weighted_expected() -> None:
    soy = SOY

    # márgenes 100, 200, 600 con pesos 1/3 vía rindes por clase
    def y_for(m):
        # m = Y*222*(1-0.11) - 250 - 20Y  => Y = (m+250)/(222*0.89-20)
        return (m + 250) / (222 * 0.89 - 20)

    custom = soy.model_copy(
        update={
            "yields": {
                YearClass.DRY: dated(y_for(100), "t/ha"),
                YearClass.NORMAL: dated(y_for(200), "t/ha"),
                YearClass.WET: dated(y_for(600), "t/ha"),
            }
        }
    )
    sc = (
        scen(2001, YearClass.DRY, weight=1 / 3),
        scen(2002, YearClass.NORMAL, weight=1 / 3),
        scen(2003, YearClass.WET, weight=1 / 3),
    )
    out = evaluate_economics(
        rot("R_SOY", Campaign(summer=Crop.SOY_1ST)),
        EconomicParameters(crops=(custom,)),
        sc,
        1,
        0.0,
        res(),
    )
    assert out.expected_mean.value == pytest.approx(300, abs=1e-6)


def test_full_matrix() -> None:
    params = EconomicParameters(crops=(SOY, crop_economics(Crop.MAIZE_EARLY)))
    sc = tuple(scen(1990 + i, weight=1 / 30) for i in range(30))
    out = evaluate_economics(
        rot("R_MS", Campaign(summer=Crop.MAIZE_EARLY), Campaign(summer=Crop.SOY_1ST)),
        params,
        sc,
        5,
        0.08,
        res(),
    )
    assert len(out.margin_matrix) == 60


def test_partial_cycle_h1_and_zero_rate() -> None:
    assert npv_by_phases([400, 300], 0.1, 1) == pytest.approx(318.18, abs=0.01)
    assert annuity_factor(0.0, 4) * 250 == pytest.approx(1000)


@settings(max_examples=40, deadline=None)
@given(
    st.lists(st.floats(min_value=-500, max_value=1500, allow_nan=False), min_size=1, max_size=4),
    st.floats(min_value=0, max_value=0.3),
    st.integers(min_value=1, max_value=20),
    st.integers(min_value=0, max_value=3),
)
def test_closed_form_equals_phases_and_rotation_invariance(exp, i, h, k) -> None:
    closed = annuity_factor(i, h) * sum(exp) / len(exp)
    assert closed == pytest.approx(npv_by_phases(exp, i, h), abs=1e-9 * max(1, abs(closed)))
    shifted = exp[k % len(exp) :] + exp[: k % len(exp)]
    assert npv_by_phases(shifted, i, h) == pytest.approx(
        npv_by_phases(exp, i, h), abs=1e-9 * max(1, abs(closed))
    )


def test_order_of_campaigns_irrelevant() -> None:
    params = EconomicParameters(crops=(SOY, crop_economics(Crop.MAIZE_EARLY)))
    sc = (scen(2008),)
    a = evaluate_economics(
        rot("R_A", Campaign(summer=Crop.MAIZE_EARLY), Campaign(summer=Crop.SOY_1ST)),
        params,
        sc,
        3,
        0.1,
        res(),
    )
    b = evaluate_economics(
        rot("R_B", Campaign(summer=Crop.SOY_1ST), Campaign(summer=Crop.MAIZE_EARLY)),
        params,
        sc,
        3,
        0.1,
        res(),
    )
    assert a.npv.value == pytest.approx(b.npv.value)


def test_missing_parameters_collected() -> None:
    wheat = crop_economics(Crop.WHEAT)
    wheat = wheat.model_copy(
        update={"yields": {k: v for k, v in wheat.yields.items() if k is not YearClass.DRY}}
    )
    maize = crop_economics(Crop.MAIZE_EARLY).model_copy(update={"freight": None})
    params = EconomicParameters(crops=(wheat, crop_economics(Crop.SOY_2ND), maize))
    r = rot(
        "R_TSM", Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND), Campaign(summer=Crop.MAIZE_EARLY)
    )
    with pytest.raises(MissingEconomicParameterError) as e:
        evaluate_economics(r, params, (scen(2008),), 1, 0.0, res())
    assert ("WHEAT", "yield_dry") in e.value.missing and (
        "MAIZE_EARLY",
        "freight",
    ) in e.value.missing


def test_explicit_zero_marketing() -> None:
    soy = SOY.model_copy(
        update={
            "marketing_cost": DatedPValue(
                value=0,
                unit="fraction",
                provenance=UserInputProvenance(),
                reference_date=date(2026, 11, 1),
            )
        }
    )
    out = evaluate_economics(
        rot("R_SOY", Campaign(summer=Crop.SOY_1ST)),
        EconomicParameters(crops=(soy,)),
        (scen(2008),),
        1,
        0.0,
        res(),
    )
    assert out.margin_matrix[0].margin.value > 371.53


def test_loss_years_and_worst() -> None:
    sc = tuple(
        scen(2008 + i, c, weight=1 / 5)
        for i, c in enumerate(
            [YearClass.DRY, YearClass.NORMAL, YearClass.WET, YearClass.DRY, YearClass.WET]
        )
    )
    bad = SOY.model_copy(
        update={
            "yields": {
                YearClass.DRY: dated(1.0, "t/ha"),
                YearClass.NORMAL: dated(3.5, "t/ha"),
                YearClass.WET: dated(4.5, "t/ha"),
            }
        }
    )
    out = evaluate_economics(
        rot("R_SOY", Campaign(summer=Crop.SOY_1ST)),
        EconomicParameters(crops=(bad,)),
        sc,
        1,
        0.0,
        res(),
    )
    assert out.loss_years.count == 2 and out.loss_years.years == (2008, 2011)
    assert out.worst_year == 2008 and out.worst_year_margin.value < 0
    assert out.lease_included is False


def test_working_capital_rent_adds_exactly() -> None:
    r = rot("R_SOY", Campaign(summer=Crop.SOY_1ST))
    a = evaluate_economics(r, EconomicParameters(crops=(SOY,)), (scen(2008),), 1, 0.0, res())
    b = evaluate_economics(
        r,
        EconomicParameters(crops=(SOY,), rent=Rent(usd_ha=dated(200, "USD/ha"))),
        (scen(2008),),
        1,
        0.0,
        res(),
    )
    assert b.working_capital_peak.value - a.working_capital_peak.value == pytest.approx(200)


def test_mixed_dates_warning() -> None:
    soy = SOY.model_copy(
        update={
            "direct_costs": DatedPValue(
                value=250,
                unit="USD/ha",
                provenance=UserInputProvenance(),
                reference_date=date(2026, 6, 15),
            )
        }
    )
    out = evaluate_economics(
        rot("R_SOY", Campaign(summer=Crop.SOY_1ST)),
        EconomicParameters(crops=(soy,)),
        (scen(2008),),
        1,
        0.0,
        res(),
    )
    assert (
        out.date_warning and "2026-06-15" in out.date_warning and "2026-11-01" in out.date_warning
    )
