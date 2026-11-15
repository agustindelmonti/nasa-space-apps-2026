"""Exhaustive rotation search (openspec change ``rotation-search``).

Generates every valid campaign and every canonical rotation of 1 to A-AGR-04 campaigns,
prunes them with the agronomic rules A-AGR-02..05, evaluates all survivors (plus the catalog
and the current rotation) with the unchanged engine in a single ``evaluate`` call, and
summarises the result: eligible ranking, Pareto front and gain over the best catalog rotation.

Deterministic: no randomness, clock or network. Ids are derived from the canonical key.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.domain.crops import (
    CROP_INFO,
    DOUBLE_CROP_SUMMER,
    Campaign,
    Crop,
    CropKind,
    Family,
    Rotation,
    Season,
)
from rastrojo.domain.engine_io import EngineInput, EngineOutput
from rastrojo.domain.results import RotationResult
from rastrojo.engine.rotation import ENGINE_VERSION, canonical_key, evaluate

GENERATOR_VERSION = "1"
SEARCH_DIR = Path(__file__).resolve().parents[3] / "data" / "fixtures" / "demo" / "search"
SEARCH_ASSUMPTIONS = ("A-AGR-02", "A-AGR-03", "A-AGR-04", "A-AGR-05")

WINTER_OPTIONS: tuple[Crop | None, ...] = (
    None,
    *(c for c in Crop if CROP_INFO[c].season is Season.WINTER),
)
SUMMER_OPTIONS: tuple[Crop | None, ...] = (
    None,
    *(c for c in Crop if CROP_INFO[c].season is Season.SUMMER),
)

# Species of a summer crop, for the "same species in a row" rule.
SUMMER_SPECIES: dict[Crop, str] = {
    Crop.SOY_1ST: "SOY",
    Crop.SOY_2ND: "SOY",
    Crop.MAIZE_EARLY: "MAIZE",
    Crop.MAIZE_LATE: "MAIZE",
}

SHORT_LABEL: dict[Crop, str] = {
    Crop.SOY_1ST: "Soja",
    Crop.SOY_2ND: "Soja 2ª",
    Crop.MAIZE_EARLY: "Maíz",
    Crop.MAIZE_LATE: "Maíz tardío",
    Crop.WHEAT: "Trigo",
    Crop.COVER_VETCH: "vicia",
    Crop.COVER_RYE: "centeno",
    Crop.COVER_OAT: "avena",
}

ROW_DIGITS = 4
RULE_NO_GRASS = "NO_GRASS_IN_CYCLE"
RULE_SUMMER_REPEAT = "SUMMER_SPECIES_REPEAT"

Key = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class SearchRules:
    double_crop_after: frozenset[Crop]
    cover_before: frozenset[Crop]
    allow_winter_only: bool
    max_length: int
    require_grass: bool
    max_consecutive_same_summer: int

    @classmethod
    def from_registry(cls, registry: AssumptionRegistry) -> SearchRules:
        a2 = dict(registry.value("A-AGR-02"))
        a3 = dict(registry.value("A-AGR-03"))
        a5 = dict(registry.value("A-AGR-05"))
        return cls(
            double_crop_after=frozenset(Crop(c) for c in a2["double_crop_after"]),
            cover_before=frozenset(Crop(c) for c in a3["cover_before"]),
            allow_winter_only=bool(a3["allow_winter_only"]),
            max_length=int(registry.value("A-AGR-04")),
            require_grass=bool(a5["require_grass"]),
            max_consecutive_same_summer=int(a5["max_consecutive_same_summer_species"]),
        )


def _campaign_key(c: Campaign) -> tuple[str, str]:
    return (c.winter.value if c.winter else "", c.summer.value if c.summer else "")


def _domain_valid(winter: Crop | None, summer: Crop | None) -> Campaign | None:
    try:
        return Campaign(winter=winter, summer=summer)
    except ValueError:
        return None


def campaign_allowed(c: Campaign, rules: SearchRules) -> bool:
    """A-AGR-02 and A-AGR-03 on top of the domain rules."""
    if c.summer is None and not rules.allow_winter_only:
        return False
    if c.summer in DOUBLE_CROP_SUMMER and c.winter not in rules.double_crop_after:
        return False
    if (
        c.winter is not None
        and CROP_INFO[c.winter].kind is CropKind.SERVICE
        and c.summer not in rules.cover_before
    ):
        return False
    # A cash winter crop is only followed by a double-crop summer crop (calendar overlap).
    return not (
        c.winter is not None
        and CROP_INFO[c.winter].kind is CropKind.CASH
        and c.summer is not None
        and c.summer not in DOUBLE_CROP_SUMMER
    )


def valid_campaigns(rules: SearchRules) -> tuple[Campaign, ...]:
    out = []
    for w, s in itertools.product(WINTER_OPTIONS, SUMMER_OPTIONS):
        c = _domain_valid(w, s)
        if c is not None and campaign_allowed(c, rules):
            out.append(c)
    return tuple(sorted(out, key=_campaign_key))


def _is_periodic(seq: Sequence[int]) -> bool:
    n = len(seq)
    return any(n % p == 0 and all(seq[i] == seq[i % p] for i in range(n)) for p in range(1, n))


def _is_canonical(seq: Sequence[int]) -> bool:
    t = tuple(seq)
    return all(t <= t[k:] + t[:k] for k in range(1, len(t)))


def canonical_sequences(n_campaigns: int, max_length: int) -> list[tuple[int, ...]]:
    """Aperiodic necklaces (Lyndon words) of length 1..max_length over ``n_campaigns``."""
    out: list[tuple[int, ...]] = []
    for length in range(1, max_length + 1):
        for seq in itertools.product(range(n_campaigns), repeat=length):
            if _is_canonical(seq) and not _is_periodic(seq):
                out.append(seq)
    return out


def rotation_name(campaigns: Iterable[Campaign]) -> str:
    parts = []
    for c in campaigns:
        summer = SHORT_LABEL[c.summer] if c.summer else "Barbecho"
        if c.winter is None:
            parts.append(summer)
        elif CROP_INFO[c.winter].kind is CropKind.SERVICE:
            parts.append(f"{summer} con {SHORT_LABEL[c.winter]}")
        else:
            parts.append(f"{SHORT_LABEL[c.winter]} / {summer}")
    return " → ".join(parts)


def rotation_id_for(key: Key) -> str:
    digest = hashlib.sha256(repr(key).encode("utf-8")).hexdigest()[:8].upper()
    return f"G_{digest}"


def cycle_violations(campaigns: Sequence[Campaign], rules: SearchRules) -> tuple[str, ...]:
    """A-AGR-05 on the circular cycle."""
    out = []
    if rules.require_grass:
        crops = [c for camp in campaigns for c in (camp.winter, camp.summer) if c is not None]
        if not any(CROP_INFO[c].family is Family.GRASS for c in crops):
            out.append(RULE_NO_GRASS)
    species = [SUMMER_SPECIES[c.summer] if c.summer else None for c in campaigns]
    n = len(species)
    limit = rules.max_consecutive_same_summer
    if n > 0 and limit > 0:
        if all(s is not None and s == species[0] for s in species):
            run = float("inf")  # one species forever
        else:
            run = 0
            for start in range(n):
                k = 0
                while (
                    k < n
                    and species[(start + k) % n] is not None
                    and (species[(start + k) % n] == species[start])
                ):
                    k += 1
                run = max(run, k)
        if run > limit:
            out.append(RULE_SUMMER_REPEAT)
    return tuple(out)


@dataclass(frozen=True, slots=True)
class Generated:
    candidates: tuple[Rotation, ...]
    in_catalog: frozenset[str]
    counts: dict[str, Any]


def generate_candidates(
    rules: SearchRules, catalog: Sequence[Rotation], current: Rotation
) -> Generated:
    """All canonical rotations that pass the rules, plus the catalog and the current one."""
    campaigns = valid_campaigns(rules)
    sequences = canonical_sequences(len(campaigns), rules.max_length)
    by_key: dict[Key, Rotation] = {}
    for r in (*catalog, current):
        by_key.setdefault(canonical_key(r), r)
    in_catalog = frozenset(r.rotation_id for r in catalog)
    pruned = {RULE_NO_GRASS: 0, RULE_SUMMER_REPEAT: 0}
    kept = 0
    for seq in sequences:
        camps = tuple(campaigns[i] for i in seq)
        violations = cycle_violations(camps, rules)
        for v in violations:
            pruned[v] += 1
        if violations:
            continue
        kept += 1
        key = tuple(_campaign_key(c) for c in camps)
        if key in by_key:
            continue
        by_key[key] = Rotation(
            rotation_id=rotation_id_for(key), name=rotation_name(camps), campaigns=camps
        )
    candidates = tuple(sorted(by_key.values(), key=lambda r: r.rotation_id))
    return Generated(
        candidates=candidates,
        in_catalog=in_catalog,
        counts={
            "valid_campaigns": len(campaigns),
            "generated": len(sequences),
            "pruned_by_rule": pruned,
            "kept_by_rules": kept,
            "evaluated": len(candidates),
        },
    )


def _num(p: Any) -> float | None:
    return None if p is None else float(p.value)


def _objectives(r: RotationResult) -> tuple[float, float, float]:
    # Rounded like the published rows, so the front can be checked from the fixture alone.
    margin = round(_num(r.expected_annual_margin) or 0.0, ROW_DIGITS)
    soil = round(_num(r.soil_delta_index) or 0.0, ROW_DIGITS)
    risk = round(_num(r.risk) or 0.0, ROW_DIGITS)
    return margin, soil, risk


def pareto_front(results: Sequence[RotationResult]) -> list[str]:
    """Eligible rotations not dominated in (margin ↑, soil ↑, risk ↓). Sorted by id."""
    pts = {r.rotation_id: _objectives(r) for r in results if r.eligible and r.breakdown}
    front = []
    for rid, (m, s, k) in pts.items():
        dominated = any(
            m2 >= m and s2 >= s and k2 <= k and (m2 > m or s2 > s or k2 < k)
            for rid2, (m2, s2, k2) in pts.items()
            if rid2 != rid
        )
        if not dominated:
            front.append(rid)
    return sorted(front)


VALUE_COLUMNS = ("score", "expected_annual_margin", "soil_delta_index", "risk")


def _values(r: RotationResult) -> dict[str, Any]:
    return {
        "score": r.breakdown.total if r.breakdown else None,
        "expected_annual_margin": r.expected_annual_margin,
        "soil_delta_index": r.soil_delta_index,
        "risk": r.risk,
    }


def _columns(results: Sequence[RotationResult]) -> dict[str, dict[str, Any]]:
    """Unit and provenance per numeric column. The engine gives every row of a column the same
    unit and provenance; if that ever stops holding, fail loudly instead of mislabelling."""
    cols: dict[str, dict[str, Any]] = {}
    for name in VALUE_COLUMNS:
        meta = {
            json_key(p.unit, p.provenance) for r in results if (p := _values(r)[name]) is not None
        }
        if len(meta) != 1:
            raise ValueError(f"columna {name}: unidad o procedencia no uniforme ({len(meta)})")
        p = next(v for r in results if (v := _values(r)[name]) is not None)
        cols[name] = {"unit": p.unit, "provenance": p.provenance.model_dump(mode="json")}
    return cols


def json_key(unit: Any, provenance: Any) -> str:
    return json.dumps([str(unit), provenance.model_dump(mode="json")], sort_keys=True)


def _row(
    r: RotationResult, rank: int, campaigns: Sequence[Campaign], in_catalog: bool, pareto: bool
) -> dict[str, Any]:
    vals = _values(r)
    return {
        "rank": rank,
        "rotation_id": r.rotation_id,
        "name": r.name,
        "campaigns": [list(_campaign_key(c)) for c in campaigns],
        "in_catalog": in_catalog,
        "is_current": r.is_current,
        "pareto": pareto,
        **{
            k: None if vals[k] is None else round(float(vals[k].value), ROW_DIGITS)
            for k in VALUE_COLUMNS
        },
        "water_feasibility": r.water_feasibility.value if r.water_feasibility else None,
    }


def summarize(
    out: EngineOutput, generated: Generated, candidates: Sequence[Rotation]
) -> dict[str, Any]:
    eligible = [r for r in out.results if r.eligible and r.breakdown is not None]
    front = set(pareto_front(eligible))
    campaigns_by_id = {r.rotation_id: r.campaigns for r in candidates}
    ranking = [
        _row(
            r,
            i,
            campaigns_by_id[r.rotation_id],
            r.rotation_id in generated.in_catalog,
            r.rotation_id in front,
        )
        for i, r in enumerate(eligible, start=1)
    ]
    best = ranking[0] if ranking else None
    best_catalog = next((row for row in ranking if row["in_catalog"]), None)
    columns = _columns(eligible) if eligible else {}
    gain = None
    if best and best_catalog:
        gain = {
            "value": round(best["score"] - best_catalog["score"], 4),
            "unit": columns["score"]["unit"],
            "provenance": {
                "kind": "DERIVED",
                "method": "puntaje de la mejor encontrada menos el de la mejor del catálogo",
                "derived_from": ["rotation-search"],
            },
        }
    return {
        "generator_version": GENERATOR_VERSION,
        "engine_version": ENGINE_VERSION,
        "input_hash": out.input_hash,
        "profile_id": out.profile_id,
        "year_class_filter": out.year_class_filter.value,
        "rules": list(SEARCH_ASSUMPTIONS),
        "counts": {**generated.counts, "eligible": len(eligible), "pareto": len(front)},
        "best_found": best["rotation_id"] if best else None,
        "best_catalog": best_catalog["rotation_id"] if best_catalog else None,
        "gain_vs_catalog": gain,
        "columns": columns,
        "ranking": ranking,
    }


def run_search(inp: EngineInput, registry: AssumptionRegistry) -> dict[str, Any]:
    """One engine call with every candidate; ``inp.candidates`` is taken as the catalog."""
    rules = SearchRules.from_registry(registry)
    generated = generate_candidates(rules, inp.candidates, inp.current_rotation)
    search_inp = inp.model_copy(update={"candidates": generated.candidates})
    out = evaluate(search_inp)
    return summarize(out, generated, (*generated.candidates, inp.current_rotation))
