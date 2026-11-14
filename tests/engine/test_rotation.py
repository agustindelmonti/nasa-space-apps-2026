from __future__ import annotations

import subprocess
import sys

import pytest

from rastrojo.domain import Campaign, Crop, Rotation, YearClassFilter, canonical_json
from rastrojo.domain.actor import MachineryWindows, SoilPriorities
from rastrojo.engine.rotation import (
    apply_year_filter,
    build_candidates,
    canonical_key,
    evaluate,
    expected_shortfall,
)
from tests.engine.engine_fixtures import demo_input, profile


def test_tail_of_one_third_exact() -> None:
    e, es = expected_shortfall([(100, 2001, 1 / 3), (200, 2002, 1 / 3), (600, 2003, 1 / 3)], 1 / 3)
    assert e == pytest.approx(300) and es == pytest.approx(100)


def test_fractional_border_scenario() -> None:
    _, es = expected_shortfall(
        [(0, 1, 0.25), (100, 2, 0.25), (200, 3, 0.25), (300, 4, 0.25)], 1 / 3
    )
    assert es == pytest.approx(25)


def test_no_variability() -> None:
    e, es = expected_shortfall([(50, 1, 0.5), (50, 2, 0.5)], 1 / 3)
    assert e == pytest.approx(es)


def test_cyclic_dedupe_current_in_catalog() -> None:
    inp = demo_input(
        current=Rotation(
            rotation_id="R_MY",
            name="mía",
            campaigns=(Campaign(summer=Crop.SOY_1ST), Campaign(summer=Crop.MAIZE_EARLY)),
        )
    )
    cands, cur = build_candidates(inp)
    assert cur == "R_MAIZE_SOY" and len(cands) == 5


def test_user_defined_current() -> None:
    mine = Rotation(
        rotation_id="R_WHEAT_SOY2",
        name="t/s2",
        campaigns=(Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND),),
    )
    out = evaluate(demo_input(current=mine))
    assert len(out.results) == 6
    assert next(r for r in out.results if r.is_current).rotation_id == "R_WHEAT_SOY2"


def test_score_breakdown_exact() -> None:
    out = evaluate(demo_input())
    for r in out.results:
        b = r.breakdown
        assert b.total.value == pytest.approx(b.npv.value + b.soil_term.value - b.risk_term.value)


def test_ranking_is_total_and_input_order_irrelevant() -> None:
    a = demo_input()
    b = a.model_copy(update={"candidates": tuple(reversed(a.candidates))})
    assert canonical_json(evaluate(a)) == canonical_json(evaluate(b))
    assert [r.rank for r in evaluate(a).results] == [1, 2, 3, 4, 5]


def test_actors_produce_different_rankings() -> None:
    owner = [r.rotation_id for r in evaluate(demo_input(profile("OWNER"))).results]
    bank = [r.rotation_id for r in evaluate(demo_input(profile("BANK"))).results]
    assert owner != bank


def test_no_double_crop_actor() -> None:
    p = profile("OWNER")
    p = p.model_copy(
        update={"constraints": p.constraints.model_copy(update={"allow_double_crop": False})}
    )
    out = evaluate(demo_input(p))
    r = next(r for r in out.results if r.rotation_id == "R_WHEAT_SOY2_MAIZE")
    assert not r.eligible and r.exclusion_reasons[0].value == "DOUBLE_CROP_NOT_ALLOWED"
    assert r.breakdown is not None


def test_two_reasons_alphabetical() -> None:
    p = profile("BANK")
    p = p.model_copy(
        update={"constraints": p.constraints.model_copy(update={"allow_cover_crop": False})}
    )
    r = next(r for r in evaluate(demo_input(p)).results if r.rotation_id == "R_MAIZE_SOY_COVER")
    assert [x.value for x in r.exclusion_reasons] == [
        "COVER_NOT_ALLOWED",
        "WORKING_CAPITAL_EXCEEDED",
    ]


def test_no_capital_cap_never_excludes() -> None:
    out = evaluate(demo_input(profile("OWNER")))
    assert all(
        "WORKING_CAPITAL_EXCEEDED" not in [x.value for x in r.exclusion_reasons]
        for r in out.results
    )


def test_missing_wheat_price_marks_ineligible_and_continues() -> None:
    inp = demo_input()
    crops = tuple(
        c.model_copy(update={"price": None}) if c.crop is Crop.WHEAT else c
        for c in inp.economics.crops
    )
    inp = inp.model_copy(update={"economics": inp.economics.model_copy(update={"crops": crops})})
    out = evaluate(inp)
    r = next(r for r in out.results if r.rotation_id == "R_WHEAT_SOY2_MAIZE")
    assert not r.eligible and r.breakdown is None
    assert any("WHEAT: price" in m.item for m in r.missing)
    assert sum(1 for r in out.results if r.breakdown is not None) == 4


def test_low_eligible_count_warning_keeps_all() -> None:
    p = profile("BANK")
    p = p.model_copy(
        update={
            "constraints": p.constraints.model_copy(
                update={"allow_cover_crop": False, "allow_double_crop": False}
            )
        }
    )
    out = evaluate(demo_input(p))
    assert "LOW_ELIGIBLE_COUNT" in out.warnings and len(out.results) == 5
    assert any(r.is_current for r in out.results)


def test_delta_vs_current_and_calendars() -> None:
    out = evaluate(demo_input())
    cur = next(r for r in out.results if r.is_current)
    assert cur.score_delta_vs_current.value == 0
    for r in out.results:
        assert r.score_delta_vs_current.value == pytest.approx(r.score - cur.score)
        assert r.bare_soil_calendar is not None and len(r.bare_soil_calendar.days_by_month) == 12
        assert r.loss_years is not None and r.rain_on_bare_soil is not None
        assert {m.year_class.value for m in r.margin_ranges} == {"DRY", "NORMAL", "WET"}


def test_priorities_only_change_soil_term() -> None:
    base = evaluate(demo_input(profile("OWNER")))
    pri = evaluate(demo_input(profile("OWNER", priorities=SoilPriorities(OM_CARBON=1.0))))
    for a, b in zip(
        sorted(base.results, key=lambda r: r.rotation_id),
        sorted(pri.results, key=lambda r: r.rotation_id),
        strict=True,
    ):
        assert a.breakdown.npv.value == b.breakdown.npv.value
        assert a.breakdown.risk_term.value == b.breakdown.risk_term.value
    assert pri.effective_soil_weights["carbon"] > base.effective_soil_weights["carbon"]


def test_null_priorities_change_nothing() -> None:
    a = evaluate(demo_input(profile("OWNER")))
    b = evaluate(demo_input(profile("OWNER", priorities=SoilPriorities())))
    assert [r.score for r in a.results] == [r.score for r in b.results]


def test_machinery_window_conflict() -> None:
    p = profile("OWNER", machinery_windows=MachineryWindows(SOWING=(10, 11)))
    r = next(r for r in evaluate(demo_input(p)).results if r.rotation_id == "R_WHEAT_SOY2_MAIZE")
    assert "MACHINERY_WINDOW_CONFLICT" in [x.value for x in r.exclusion_reasons]


def test_year_filter_dry() -> None:
    inp = demo_input(year_class_filter=YearClassFilter.DRY)
    out = evaluate(inp)
    assert "YEAR_CLASS_FILTER_APPLIED:DRY" in out.warnings
    assert len(out.years_used) < len(inp.scenarios)
    assert sum(
        s.weight for s in apply_year_filter(inp.scenarios, YearClassFilter.DRY)
    ) == pytest.approx(1)


def test_canonical_key_cyclic() -> None:
    a = Rotation(
        rotation_id="R_A",
        name="a",
        campaigns=(Campaign(summer=Crop.SOY_1ST), Campaign(summer=Crop.MAIZE_EARLY)),
    )
    b = Rotation(
        rotation_id="R_B",
        name="b",
        campaigns=(Campaign(summer=Crop.MAIZE_EARLY), Campaign(summer=Crop.SOY_1ST)),
    )
    assert canonical_key(a) == canonical_key(b)


def test_same_input_same_bytes_two_processes() -> None:
    code = (
        "import sys\nfrom rastrojo.domain import canonical_json\nfrom rastrojo.engine.rotation import evaluate\n"
        "from tests.engine.engine_fixtures import demo_input\n"
        "sys.stdout.buffer.write(canonical_json(evaluate(demo_input())))"
    )
    outs = [
        subprocess.run([sys.executable, "-c", code], capture_output=True, check=True).stdout
        for _ in range(2)
    ]
    assert outs[0] == outs[1] and len(outs[0]) > 10000


def test_engine_does_not_touch_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    inp = demo_input()

    def boom(*a, **k):
        raise AssertionError("el motor intentó abrir un socket")

    monkeypatch.setattr(socket.socket, "connect", boom)
    assert evaluate(inp).results
