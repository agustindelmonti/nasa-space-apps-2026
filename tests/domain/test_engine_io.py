from __future__ import annotations

import pytest
from pydantic import ValidationError

from rastrojo.domain import EngineInput, EngineOutput, WaterFeasibility, WaterInputs
from tests.domain.factories import breakdown, engine_input, pv, result, weather


def test_breakdown_consistent() -> None:
    b = breakdown(900, 60, 40)
    assert b.total.value == pytest.approx(b.npv.value + b.soil_term.value - b.risk_term.value)


def test_breakdown_inconsistent_rejected() -> None:
    b = breakdown(900, 60, 40)
    with pytest.raises(ValidationError, match="desglose inconsistente"):
        type(b).model_validate({**b.model_dump(), "total": pv(1000, "USD/ha").model_dump()})


def test_delta_vs_current() -> None:
    current = result("R_SOY_MONO", 2, 900, 900, is_current=True)
    other = result("R_MAIZE_SOY", 1, 965, 900)
    out = EngineOutput(engine_version="0.1.0", input_hash="a" * 64, results=(other, current))
    assert out.results[0].score_delta_vs_current.value == pytest.approx(65)
    assert out.results[1].score_delta_vs_current.value == 0


def test_margin_range_by_class() -> None:
    r = result("R_MAIZE_SOY", 1, 965, 900)
    assert {m.year_class.value for m in r.margin_ranges} == {"DRY", "NORMAL", "WET"}
    assert all(m.expected.provenance.kind == "DERIVED" for m in r.margin_ranges)


def test_unknown_feasibility_distinct() -> None:
    r = result("R_MAIZE_SOY", 1, 965, 900, water_feasibility=WaterFeasibility.UNKNOWN)
    assert r.water_feasibility is WaterFeasibility.UNKNOWN
    assert WaterFeasibility.UNKNOWN != WaterFeasibility.NOT_FEASIBLE


def test_calendars_have_12_months() -> None:
    r = result("R_MAIZE_SOY", 1, 965, 900)
    assert len(r.bare_soil_calendar.days_by_month) == 12


def test_precomputed_water_state_rejected() -> None:
    data = engine_input().model_dump()
    data["water_feasibility"] = "FEASIBLE"
    with pytest.raises(ValidationError, match="water_feasibility"):
        EngineInput.model_validate(data)


def test_optional_inputs_absent() -> None:
    inp = engine_input()
    assert inp.water_inputs.grace_tws_anomaly is None
    assert inp.water_inputs.ndvi_monthly is None


def test_resolved_assumptions_in_hash() -> None:
    base = engine_input()
    other = engine_input(resolved_assumptions={})
    assert "A-WAT-01" in base.canonical_data()["resolved_assumptions"]
    assert base.input_hash() != other.input_hash()


def test_list_order_irrelevant_for_hash() -> None:
    base = engine_input()
    shuffled = engine_input(
        candidates=tuple(reversed(base.candidates)),
        scenarios=tuple(reversed(base.scenarios)),
        water_inputs=WaterInputs(weather=(weather(2014), weather(2008))),
    )
    assert base.input_hash() == shuffled.input_hash()


def test_output_requires_one_current() -> None:
    a = result("R_MAIZE_SOY", 1, 965, 900)
    with pytest.raises(ValidationError, match="actual"):
        EngineOutput(engine_version="0.1.0", input_hash="a" * 64, results=(a,))


def test_output_hash_format() -> None:
    current = result("R_SOY_MONO", 1, 900, 900, is_current=True)
    with pytest.raises(ValidationError, match="SHA-256"):
        EngineOutput(engine_version="0.1.0", input_hash="xyz", results=(current,))
