from __future__ import annotations

import json
from pathlib import Path

import pytest

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import (
    CATALOG,
    CATALOG_BY_ID,
    PROFILE_ASSUMPTIONS,
    actor_profile,
    build_engine_input,
)
from rastrojo.application.search import (
    RULE_NO_GRASS,
    RULE_SUMMER_REPEAT,
    SEARCH_DIR,
    SearchRules,
    canonical_sequences,
    cycle_violations,
    generate_candidates,
    rotation_id_for,
    run_search,
    valid_campaigns,
)
from rastrojo.domain.climate import YearClassFilter
from rastrojo.domain.crops import CROP_INFO, DOUBLE_CROP_SUMMER, Campaign, Crop, CropKind
from rastrojo.engine.rotation import canonical_key


@pytest.fixture(scope="module")
def reg() -> AssumptionRegistry:
    return AssumptionRegistry.load()


@pytest.fixture(scope="module")
def rules(reg: AssumptionRegistry) -> SearchRules:
    return SearchRules.from_registry(reg)


def test_double_crop_only_after_wheat(rules: SearchRules) -> None:
    camps = valid_campaigns(rules)
    for c in camps:
        if c.summer in DOUBLE_CROP_SUMMER:
            assert c.winter is Crop.WHEAT
        if c.winter is Crop.WHEAT:
            assert c.summer in DOUBLE_CROP_SUMMER


def test_cover_only_before_first_summer_crop(rules: SearchRules) -> None:
    camps = valid_campaigns(rules)
    covers = [c for c in camps if c.winter and CROP_INFO[c.winter].kind is CropKind.SERVICE]
    assert covers
    assert all(c.summer in {Crop.SOY_1ST, Crop.MAIZE_EARLY} for c in covers)
    assert all(c.summer is not None for c in camps)
    assert len(camps) == 10


def test_equivalent_cycles_and_periodic_sequences() -> None:
    seqs = canonical_sequences(3, 3)
    assert (0, 1, 2) in seqs
    assert (1, 2, 0) not in seqs and (2, 0, 1) not in seqs
    assert (0, 0) not in seqs and (1, 1, 1) not in seqs
    # Collares aperiódicos (palabras de Lyndon) de largo 1 a 3 sobre 10 campañas.
    assert len(canonical_sequences(10, 3)) == 10 + 45 + 330


def test_ids_are_stable() -> None:
    key = (("", "MAIZE_EARLY"), ("WHEAT", "SOY_2ND"))
    assert rotation_id_for(key) == rotation_id_for(key)
    assert rotation_id_for(key).startswith("G_")


def test_continuous_soy_is_pruned_unless_current_or_catalog(rules: SearchRules) -> None:
    soy = (Campaign(summer=Crop.SOY_1ST),)
    assert RULE_NO_GRASS in cycle_violations(soy, rules)
    assert RULE_SUMMER_REPEAT in cycle_violations(soy, rules)
    three_maize = (
        Campaign(summer=Crop.MAIZE_EARLY),
        Campaign(winter=Crop.COVER_RYE, summer=Crop.MAIZE_EARLY),
        Campaign(winter=Crop.WHEAT, summer=Crop.MAIZE_LATE),
    )
    assert RULE_SUMMER_REPEAT in cycle_violations(three_maize, rules)
    # Circular: soja, maíz, soja repite soja dos veces al cerrar el ciclo (permitido).
    wrap = (
        Campaign(summer=Crop.SOY_1ST),
        Campaign(summer=Crop.MAIZE_EARLY),
        Campaign(winter=Crop.COVER_VETCH, summer=Crop.SOY_1ST),
    )
    assert cycle_violations(wrap, rules) == ()

    gen = generate_candidates(rules, CATALOG, CATALOG_BY_ID["R_SOY_MONO"])
    keys = {canonical_key(r) for r in gen.candidates}
    assert all(canonical_key(r) in keys for r in CATALOG)
    ids = {r.rotation_id for r in gen.candidates}
    assert set(CATALOG_BY_ID) <= ids
    assert len(keys) == len(gen.candidates)
    assert gen.counts["pruned_by_rule"][RULE_SUMMER_REPEAT] > 0


def _small_registry(tmp_path: Path) -> AssumptionRegistry:
    text = Path("data/assumptions.yaml").read_text(encoding="utf-8")
    marker = "- assumption_id: A-AGR-04"
    head, tail = text.split(marker, 1)
    tail = tail.replace("  value: 3\n", "  value: 1\n", 1)
    p = tmp_path / "a.yaml"
    p.write_text(head + marker + tail, encoding="utf-8")
    return AssumptionRegistry.load(p)


def test_search_best_not_worse_than_catalog_and_deterministic(tmp_path: Path) -> None:
    reg = _small_registry(tmp_path)
    inp = build_engine_input(actor_profile(reg, "OWNER"), registry=reg)
    a = run_search(inp, reg)
    b = run_search(inp, reg)
    assert a == b
    ranking = a["ranking"]
    best_catalog = next(r for r in ranking if r["in_catalog"])
    assert ranking[0]["score"] >= best_catalog["score"]
    assert a["gain_vs_catalog"]["value"] >= 0
    assert a["columns"]["score"]["provenance"]["kind"] == "DERIVED"
    _assert_pareto(ranking)


def test_water_not_feasible_does_not_compete(tmp_path: Path) -> None:
    reg = _small_registry(tmp_path)
    inp = build_engine_input(
        actor_profile(reg, "OWNER"), year_class_filter=YearClassFilter.DRY, registry=reg
    )
    a = run_search(inp, reg)
    assert all(r["water_feasibility"] in {"FEASIBLE", "RISKY"} for r in a["ranking"])
    assert a["counts"]["water_excluded"] >= 0
    assert a["counts"]["eligible"] == len(a["ranking"])


def _assert_pareto(ranking: list[dict[str, object]]) -> None:
    def obj(r: dict[str, object]) -> tuple[float, float, float]:
        return (float(r["expected_annual_margin"]), float(r["soil_delta_index"]), -float(r["risk"]))  # type: ignore[arg-type]

    front = [r for r in ranking if r["pareto"]]
    assert front
    for f in front:
        fo = obj(f)
        for r in ranking:
            ro = obj(r)
            dominates = all(x >= y for x, y in zip(ro, fo, strict=True)) and ro != fo
            assert not dominates, f"{r['rotation_id']} domina a {f['rotation_id']}"
    for r in ranking:
        if not r["pareto"]:
            ro = obj(r)
            assert any(
                all(x >= y for x, y in zip(obj(f), ro, strict=True)) and obj(f) != ro
                for f in ranking
            )


@pytest.mark.parametrize("actor", sorted(PROFILE_ASSUMPTIONS))
@pytest.mark.parametrize("flt", [f.value for f in YearClassFilter])
def test_precomputed_fixture_is_fresh(reg: AssumptionRegistry, actor: str, flt: str) -> None:
    """El precálculo corresponde a la entrada actual (si no, correr precompute_search.py)."""
    data = json.loads((SEARCH_DIR / f"{actor}_{flt}.json").read_text(encoding="utf-8"))
    inp = build_engine_input(
        actor_profile(reg, actor), year_class_filter=YearClassFilter(flt), registry=reg
    )
    gen = generate_candidates(SearchRules.from_registry(reg), inp.candidates, inp.current_rotation)
    assert data["input_hash"] == inp.model_copy(update={"candidates": gen.candidates}).input_hash()
    assert data["profile_id"] == actor and data["year_class_filter"] == flt
    ranking = data["ranking"]
    assert all(r["water_feasibility"] in {"FEASIBLE", "RISKY"} for r in ranking)
    if ranking:
        best_catalog = next(r for r in ranking if r["in_catalog"])
        assert ranking[0]["score"] >= best_catalog["score"]
        _assert_pareto(ranking)
