from __future__ import annotations

import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from rastrojo.application.assumptions import AssumptionRegistry, resolve
from rastrojo.domain import Campaign, Crop, Rotation, canonical_json
from rastrojo.domain.provenance import UserInputProvenance
from rastrojo.engine.soil import (
    SOIL_ASSUMPTIONS,
    InvalidSoilAssumptionError,
    MissingSoilAssumptionError,
    evaluate_soil,
)
from tests.domain.factories import pv
from tests.engine.water_fixtures import inputs, scenarios_and_weather


def res():
    return resolve(AssumptionRegistry.load(), SOIL_ASSUMPTIONS)


def rot(rid: str, *campaigns: Campaign) -> Rotation:
    return Rotation(rotation_id=rid, name=rid, campaigns=campaigns)


SOY = rot("R_SOY_MONO", Campaign(summer=Crop.SOY_1ST))
SOY_RYE = rot("R_SOY_COVER", Campaign(winter=Crop.COVER_RYE, summer=Crop.SOY_1ST))
MAIZE_SOY = rot("R_MAIZE_SOY", Campaign(summer=Crop.MAIZE_EARLY), Campaign(summer=Crop.SOY_1ST))
TSM = rot(
    "R_WHEAT_SOY2_MAIZE",
    Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND),
    Campaign(summer=Crop.MAIZE_EARLY),
)
DIVERSE = rot(
    "R_DIVERSE",
    Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND),
    Campaign(winter=Crop.COVER_VETCH, summer=Crop.MAIZE_EARLY),
)


def comp(r, name):
    return next(c for c in evaluate_soil(r, res()).components if c.name == name)


def test_index_within_bounds_and_breakdown_sums() -> None:
    for r in (SOY, SOY_RYE, MAIZE_SOY, TSM, DIVERSE):
        s = evaluate_soil(r, res())
        assert -100 <= s.index.value <= 100
        assert math.fsum(c.contribution.value for c in s.components) == pytest.approx(
            s.index.value, abs=1e-5
        )
        assert math.fsum(c.points.value for c in s.by_campaign) == pytest.approx(
            s.index.value, abs=1e-5
        )
        assert s.index.provenance.kind == "DERIVED"


def test_soy_mono_bare_winter() -> None:
    s = evaluate_soil(SOY, res())
    # julio: soja cosechada en abril + 60 días de rastrojo => invierno desnudo
    assert s.bare_soil_calendar.days_by_month[6] == 31
    assert s.bare_soil_calendar.days_by_month[0] == 0  # enero con soja


def test_cover_crop_covers_winter() -> None:
    a = evaluate_soil(SOY, res()).bare_soil_calendar.days_by_month
    b = evaluate_soil(SOY_RYE, res()).bare_soil_calendar.days_by_month
    assert b[6] < a[6]


def test_overlap_not_double_counted() -> None:
    assert comp(TSM, "cover").raw.value <= 1.0


def test_grass_more_carbon_than_legume() -> None:
    assert comp(MAIZE_SOY, "carbon").raw.value > comp(SOY, "carbon").raw.value


def test_vetch_as_legume_service_adds_nitrogen() -> None:
    vetch = rot("R_SOY_VETCH", Campaign(winter=Crop.COVER_VETCH, summer=Crop.SOY_1ST))
    assert comp(vetch, "nitrogen").raw.value > comp(SOY, "nitrogen").raw.value


def test_soy_mono_weeds_minimum_and_diverse_higher() -> None:
    assert comp(SOY, "weeds").score == pytest.approx(-1.0)
    assert comp(DIVERSE, "weeds").score > comp(MAIZE_SOY, "weeds").score


def test_rye_over_soy_monotonic_except_nitrogen() -> None:
    a = {c.name: c.score for c in evaluate_soil(SOY, res()).components}
    b = {c.name: c.score for c in evaluate_soil(SOY_RYE, res()).components}
    for k in ("cover", "carbon", "weeds", "roots"):
        assert b[k] >= a[k]
    # Documentado: el centeno puede inmovilizar N (A-SOIL-06 negativo), por eso N no está garantizado.
    assert b["nitrogen"] <= a["nitrogen"]


ROTS = [SOY, SOY_RYE, MAIZE_SOY, TSM, DIVERSE]


@settings(max_examples=20, deadline=None)
@given(st.sampled_from(ROTS), st.integers(min_value=0, max_value=3))
def test_cycle_rotation_invariance(r: Rotation, k: int) -> None:
    n = len(r.campaigns)
    shifted = r.model_copy(update={"campaigns": r.campaigns[k % n :] + r.campaigns[: k % n]})
    assert evaluate_soil(r, res()).index.value == pytest.approx(
        evaluate_soil(shifted, res()).index.value, abs=1e-9
    )


def test_invalid_weights() -> None:
    with pytest.raises(InvalidSoilAssumptionError):
        evaluate_soil(
            SOY,
            res(),
            effective_weights={
                "cover": 0.5,
                "carbon": 0.5,
                "nitrogen": 0.5,
                "weeds": 0,
                "roots": 0,
            },
        )


def test_missing_rye_carbon() -> None:
    r = res()
    table = dict(r["A-SOIL-04"].value)
    del table["COVER_RYE"]
    r["A-SOIL-04"] = r["A-SOIL-04"].model_copy(update={"value": table})
    with pytest.raises(MissingSoilAssumptionError) as e:
        evaluate_soil(SOY_RYE, r)
    assert ("A-SOIL-04", "COVER_RYE") in e.value.missing


def test_priority_effective_weights() -> None:
    base = evaluate_soil(MAIZE_SOY, res())
    carbon_heavy = evaluate_soil(
        MAIZE_SOY,
        res(),
        effective_weights={
            "cover": 0.1,
            "carbon": 0.6,
            "nitrogen": 0.1,
            "weeds": 0.1,
            "roots": 0.1,
        },
    )
    assert carbon_heavy.index.value != base.index.value


def test_rain_on_bare_soil() -> None:
    scen, wx = scenarios_and_weather(30)
    a = evaluate_soil(SOY, res(), scen, inputs(wx))
    b = evaluate_soil(SOY_RYE, res(), scen, inputs(wx))
    assert a.rain_on_bare_soil.value > 0
    assert b.rain_on_bare_soil.value < a.rain_on_bare_soil.value
    assert a.index.value == evaluate_soil(SOY, res()).index.value  # el índice no cambia


def test_ndvi_evidence_only_for_current() -> None:
    scen, wx = scenarios_and_weather(30)
    ndvi = tuple(
        pv(0.2 if m in (5, 6, 7, 8) else 0.6, "index", UserInputProvenance()) for m in range(12)
    )
    inp = inputs(wx).model_copy(update={"ndvi_monthly": ndvi})
    cur = evaluate_soil(SOY, res(), scen, inp, is_current=True)
    assert cur.observed_bare_months is not None and cur.evidence
    alt = evaluate_soil(SOY_RYE, res(), scen, inp, is_current=False)
    assert alt.observed_bare_months is None


def test_without_ndvi_summary() -> None:
    cur = evaluate_soil(SOY, res(), is_current=True)
    assert any(m.item == "NDVI histórico del lote" for m in cur.missing)


def test_deterministic() -> None:
    assert canonical_json(evaluate_soil(DIVERSE, res())) == canonical_json(
        evaluate_soil(DIVERSE, res())
    )
