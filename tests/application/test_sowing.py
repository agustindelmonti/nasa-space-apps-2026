"""¿Me conviene sembrar?: decisión sobre la salida real del motor (lote demo, NASA POWER cacheado)."""

from __future__ import annotations

from functools import cache

import pytest

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import CATALOG, actor_profile, build_engine_input, demo_economics
from rastrojo.application.explanations import parse_ar_numbers
from rastrojo.application.sowing import sowing_decision, usd_per_qq
from rastrojo.domain.results import ExclusionReason
from rastrojo.engine.rotation import evaluate

NAMES = {r.rotation_id: r.name for r in CATALOG}


@cache
def _reg() -> AssumptionRegistry:
    return AssumptionRegistry.load()


@cache
def _out(actor: str = "OWNER"):
    reg = _reg()
    return evaluate(build_engine_input(actor_profile(reg, actor), registry=reg))


def _decide(actor: str = "OWNER", **kw):
    reg = _reg()
    return sowing_decision(_out(actor), NAMES, reg, demo_economics(reg), **kw)


def test_cheap_rent_says_sow_and_expensive_rent_says_rent() -> None:
    cheap = _decide(rent_qq_ha=0)
    assert cheap.verdict in ("SOW", "SOW_WITH_RISK")
    assert cheap.headline.startswith("Sí, conviene sembrar")
    dear = _decide(rent_qq_ha=40)
    assert dear.verdict == "RENT_BETTER"
    assert dear.vs_rent is not None and dear.vs_rent.value < 0


def test_breakeven_rent_is_where_the_answer_flips() -> None:
    d = _decide()
    assert d.breakeven_rent_qq is not None
    even = d.breakeven_rent_qq.value
    assert _decide(rent_qq_ha=even - 0.5).verdict in ("SOW", "SOW_WITH_RISK")
    assert _decide(rent_qq_ha=even + 0.5).verdict == "RENT_BETTER"


def test_rent_is_valued_with_the_engine_soy_price() -> None:
    reg = _reg()
    d = _decide(rent_qq_ha=10)
    assert d.rent.value == pytest.approx(10 * usd_per_qq(reg, demo_economics(reg)))
    assert d.rent_qq == pytest.approx(10)


def test_default_alternatives_are_assumptions() -> None:
    d = _decide()
    assert d.fallow_cost.provenance.kind == "ASSUMPTION"
    assert "A-ECO-05" in d.rent.provenance.derived_from  # type: ignore[union-attr]
    assert {"A-ECO-05", "A-ECO-06", "A-ACT-10"} <= set(d.assumptions)


def test_tenant_question_is_whether_to_keep_renting() -> None:
    d = _decide("TENANT", rent_qq_ha=0)
    assert "seguir arrendando" in d.headline
    assert any("arrendatario" in r for r in d.reasons)


def test_no_eligible_rotation_means_dont_sow() -> None:
    out = _out()
    blocked = tuple(
        r.model_copy(
            update={"eligible": False, "exclusion_reasons": (ExclusionReason.MISSING_PARAMETERS,)}
        )
        for r in out.results
    )
    reg = _reg()
    d = sowing_decision(
        out.model_copy(update={"results": blocked}), NAMES, reg, demo_economics(reg)
    )
    assert d.verdict == "DONT_SOW"
    assert d.rotation_id is None


def test_deterministic() -> None:
    assert _decide().model_dump() == _decide().model_dump()


def test_numbers_in_text_come_from_the_decision() -> None:
    d = _decide()
    assert d.expected_margin is not None and d.vs_rent is not None and d.vs_fallow is not None
    assert d.breakeven_rent_qq is not None
    allowed = {
        round(abs(v))
        for v in (d.expected_margin.value, d.rent.value, d.vs_rent.value, d.vs_fallow.value)
    }
    allowed |= {d.campaigns_below_rent, d.campaigns_total}
    for line in (d.headline, *d.reasons):
        for n in parse_ar_numbers(line):
            if n == round(d.breakeven_rent_qq.value, 1):
                continue
            assert round(n) in allowed, (n, line)
