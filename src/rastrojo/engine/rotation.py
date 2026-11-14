"""Motor de rotaciones: score = VAN + α·ΔSuelo − λ·Riesgo, ranking estable y salida auditable.

Función pura de `EngineInput`: sin red, archivos, entorno, reloj, azar ni LLM.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from rastrojo.domain.climate import ClimateScenario, YearClassFilter
from rastrojo.domain.crops import CROP_INFO, Crop, Rotation
from rastrojo.domain.engine_io import EngineInput, EngineOutput, ResolvedAssumption
from rastrojo.domain.provenance import DerivedProvenance, PValue
from rastrojo.domain.results import (
    AnnualMargin,
    Benefit,
    ExclusionReason,
    MissingInfo,
    Risk,
    RiskType,
    RotationResult,
    ScoreBreakdown,
    Severity,
    WaterAdjustment,
    WaterFeasibility,
)
from rastrojo.engine.economics import (
    Adjustment,
    AdjustmentKey,
    EconomicsResult,
    MissingEconomicParameterError,
    annuity_factor,
    evaluate_economics,
)
from rastrojo.engine.soil import (
    COMPONENTS,
    MissingSoilAssumptionError,
    SoilImpact,
    evaluate_soil,
)
from rastrojo.engine.water import WaterAssessment, evaluate_rotation

ENGINE_VERSION = "0.1.0"
MIN_OPTIONS = 3
SCORE_DIGITS = 2

_COMPONENT_LABELS = {
    "cover": "Cobertura del suelo",
    "carbon": "Aporte de carbono (rastrojo)",
    "nitrogen": "Balance de nitrógeno",
    "weeds": "Corte de ciclos de malezas",
    "roots": "Raíces contra la compactación",
}
_PRIORITY_TO_COMPONENT = {
    "EROSION_COVER": "cover",
    "OM_CARBON": "carbon",
    "NITROGEN": "nitrogen",
    "WEED_CONTROL": "weeds",
    "ROOTS": "roots",
}


def _derived(method: str, *inputs: str) -> DerivedProvenance:
    return DerivedProvenance(method=method, derived_from=tuple(inputs) or ("rastrojo.engine",))


def _v(resolved: Mapping[str, ResolvedAssumption], aid: str) -> Any:
    return resolved[aid].value


# ---------------------------------------------------------------------------
# Candidatas
# ---------------------------------------------------------------------------


def canonical_key(rotation: Rotation) -> tuple[tuple[str, str], ...]:
    """Forma canónica cíclica: la rotación mínima lexicográfica entre sus L desplazamientos."""
    rows = [
        (c.winter.value if c.winter else "", c.summer.value if c.summer else "")
        for c in rotation.campaigns
    ]
    return min(tuple(rows[k:] + rows[:k]) for k in range(len(rows)))


def build_candidates(inp: EngineInput) -> tuple[list[Rotation], str]:
    """Catálogo de la entrada más la actual (deduplicada por equivalencia cíclica)."""
    by_id = sorted(inp.candidates, key=lambda r: r.rotation_id)
    current_key = canonical_key(inp.current_rotation)
    for r in by_id:
        if canonical_key(r) == current_key:
            return by_id, r.rotation_id
    return sorted(
        [*by_id, inp.current_rotation], key=lambda r: r.rotation_id
    ), inp.current_rotation.rotation_id


# ---------------------------------------------------------------------------
# Filtro por clase de año
# ---------------------------------------------------------------------------


def apply_year_filter(
    scenarios: tuple[ClimateScenario, ...], flt: YearClassFilter
) -> tuple[ClimateScenario, ...]:
    if flt is YearClassFilter.ALL:
        return scenarios
    selected = [s for s in scenarios if s.annual_class.value == flt.value]
    total = math.fsum(s.weight for s in selected)
    if not selected or total <= 0:
        return ()
    return tuple(s.model_copy(update={"weight": s.weight / total}) for s in selected)


# ---------------------------------------------------------------------------
# Riesgo
# ---------------------------------------------------------------------------


def expected_shortfall(margins: list[tuple[float, int, float]], q: float) -> tuple[float, float]:
    """(E, ES) con cola de peso q y escenario de borde fraccionado. margins: (margen, año, peso)."""
    ordered = sorted(margins, key=lambda m: (m[0], m[1]))
    e = math.fsum(m * w for m, _, w in ordered)
    acc = 0.0
    tail: list[float] = []
    for m, _, w in ordered:
        if acc >= q - 1e-15:
            break
        take = min(w, q - acc)
        tail.append(take * m)
        acc += take
    es = math.fsum(tail) / q if q > 0 else e
    return e, es


def risk_value(
    eco: EconomicsResult,
    scenarios: tuple[ClimateScenario, ...],
    q: float,
    i: float,
    h: int,
    cycle: int,
) -> float:
    weights = {s.campaign_start_year: s.weight for s in scenarios}
    shortfalls: list[float] = []
    for p in range(cycle):
        rows = [
            (m.margin.value, m.campaign_start_year, weights[m.campaign_start_year])
            for m in eco.margin_matrix
            if m.campaign_index == p
        ]
        e, es = expected_shortfall(rows, q)
        shortfalls.append(max(0.0, e - es))
    return annuity_factor(i, h) * math.fsum(shortfalls) / cycle


# ---------------------------------------------------------------------------
# Pesos efectivos de ΔSuelo
# ---------------------------------------------------------------------------


def effective_soil_weights(inp: EngineInput) -> dict[str, float]:
    base = {k: float(v) for k, v in dict(_v(inp.resolved_assumptions, "A-SOIL-01")).items()}
    pr = inp.profile.priorities
    if pr is None:
        return base
    m = (
        float(_v(inp.resolved_assumptions, "A-ACT-07"))
        if "A-ACT-07" in inp.resolved_assumptions
        else 1.0
    )
    raw = {k: base[k] for k in COMPONENTS}
    for name, comp in _PRIORITY_TO_COMPONENT.items():
        p = getattr(pr, name) or 0.0
        raw[comp] = base[comp] * (1.0 + m * p)
    total = math.fsum(raw.values())
    return {k: raw[k] / total for k in COMPONENTS}


# ---------------------------------------------------------------------------
# Restricciones
# ---------------------------------------------------------------------------


def _month(spec: str) -> int:
    raw = str(spec)
    if raw.startswith("+1-"):
        raw = raw[3:]
    return int(raw.split("-")[0])


def constraint_reasons(
    rotation: Rotation, inp: EngineInput, capital_peak: float | None
) -> list[ExclusionReason]:
    reasons: set[ExclusionReason] = set()
    c = inp.profile.constraints
    if not c.allow_double_crop and any(camp.is_double_crop for camp in rotation.campaigns):
        reasons.add(ExclusionReason.DOUBLE_CROP_NOT_ALLOWED)
    if not c.allow_cover_crop and any(camp.has_cover_crop for camp in rotation.campaigns):
        reasons.add(ExclusionReason.COVER_NOT_ALLOWED)
    cap = c.max_working_capital_usd_ha
    if cap is not None and capital_peak is not None and capital_peak > cap.value:
        reasons.add(ExclusionReason.WORKING_CAPITAL_EXCEEDED)
    mw = inp.profile.machinery_windows
    if mw is not None and "A-AGR-01" in inp.resolved_assumptions:
        cal = dict(_v(inp.resolved_assumptions, "A-AGR-01"))
        for camp in rotation.campaigns:
            for crop in (camp.winter, camp.summer):
                if crop is None or crop.value not in cal:
                    continue
                if mw.SOWING is not None and _month(cal[crop.value]["sow"]) not in mw.SOWING:
                    reasons.add(ExclusionReason.MACHINERY_WINDOW_CONFLICT)
                if mw.HARVEST is not None and _month(cal[crop.value]["harvest"]) not in mw.HARVEST:
                    reasons.add(ExclusionReason.MACHINERY_WINDOW_CONFLICT)
    return sorted(reasons, key=lambda r: r.value)


# ---------------------------------------------------------------------------
# Evaluación de una candidata
# ---------------------------------------------------------------------------


def _adjustments(
    wat: WaterAssessment,
) -> tuple[dict[AdjustmentKey, Adjustment], list[WaterAdjustment]]:
    adj: dict[AdjustmentKey, Adjustment] = {}
    rows: list[WaterAdjustment] = []
    for st in wat.crop_status:
        # El tipo de año (seco, normal, húmedo) ya fija el rinde. El balance de agua solo lo
        # baja a rinde de año seco cuando el estrés es severo, o cuando el perfil no se
        # recargó para el cultivo de verano del doble cultivo o del servicio. El estrés
        # moderado queda como riesgo, sin castigar el rinde dos veces.
        effect: Adjustment = "NONE"
        if st.status is WaterFeasibility.NOT_FEASIBLE or (
            st.status is WaterFeasibility.RISKY and st.recharge_limited
        ):
            effect = "FORCE_DRY"
        if effect != "NONE":
            adj[(st.crop, st.campaign_index, st.campaign_start_year)] = effect
            rows.append(
                WaterAdjustment(
                    crop=st.crop,
                    campaign_index=st.campaign_index,
                    scenario_year=st.campaign_start_year,
                    status=st.status,
                    effect=effect,
                )
            )
    return adj, rows


def _never_feasible(wat: WaterAssessment) -> bool:
    by_crop: dict[tuple[Crop, int], list[WaterFeasibility]] = {}
    for st in wat.crop_status:
        if st.status is not WaterFeasibility.UNKNOWN:
            by_crop.setdefault((st.crop, st.campaign_index), []).append(st.status)
    return any(v and all(s is WaterFeasibility.NOT_FEASIBLE for s in v) for v in by_crop.values())


def _level(freq: float, resolved: Mapping[str, ResolvedAssumption]) -> Severity:
    lv = dict(_v(resolved, "A-CLI-07"))
    if freq >= float(lv["high"]):
        return Severity.HIGH
    if freq >= float(lv["medium"]):
        return Severity.MEDIUM
    return Severity.LOW


def evaluate_candidate(
    rotation: Rotation,
    inp: EngineInput,
    scenarios: tuple[ClimateScenario, ...],
    water_resolved: dict[str, ResolvedAssumption],
    weights: dict[str, float],
    is_current: bool,
) -> dict[str, Any]:
    prof = inp.profile
    h, i = prof.horizon, prof.discount_rate.value
    alpha, lam = prof.soil_weight_alpha.value, prof.risk_aversion_lambda.value
    q = float(_v(inp.resolved_assumptions, "A-ACT-05"))
    missing: list[MissingInfo] = []
    reasons: list[ExclusionReason] = []

    wat = evaluate_rotation(rotation, inp.soil, scenarios, inp.water_inputs, water_resolved)
    adj, adj_rows = _adjustments(wat)
    feasibility = wat.status
    if feasibility is not WaterFeasibility.UNKNOWN and _never_feasible(wat):
        feasibility = WaterFeasibility.NOT_FEASIBLE
        reasons.append(ExclusionReason.WATER_NEVER_FEASIBLE)
    unknown_years = sorted(
        {s.campaign_start_year for s in wat.crop_status if s.status is WaterFeasibility.UNKNOWN}
    )
    if unknown_years and feasibility is not WaterFeasibility.UNKNOWN:
        missing.append(
            MissingInfo(
                item=f"evaluación hídrica de los años {', '.join(str(y) for y in unknown_years)}",
                why_it_matters="Esos años no tienen clima completo y no se ajustaron por agua.",
                how_to_get="Completar la serie diaria de NASA POWER para esos años.",
            )
        )
    missing += list(wat.missing)

    eco: EconomicsResult | None = None
    try:
        eco = evaluate_economics(
            rotation, inp.economics, scenarios, h, i, inp.resolved_assumptions, adj
        )
    except MissingEconomicParameterError as exc:
        reasons.append(ExclusionReason.MISSING_PARAMETERS)
        for crop, param in exc.missing:
            missing.append(
                MissingInfo(
                    item=f"{crop}: {param}",
                    why_it_matters="Sin este parámetro no se puede calcular el margen de la rotación.",
                    how_to_get="Cargar el valor con su fuente y fecha (pizarra, márgenes publicados o dato del productor).",
                )
            )

    soil: SoilImpact | None = None
    try:
        soil = evaluate_soil(
            rotation, inp.resolved_assumptions, scenarios, inp.water_inputs, weights, is_current
        )
    except MissingSoilAssumptionError as exc:
        reasons.append(ExclusionReason.MISSING_PARAMETERS)
        for aid, what in exc.missing:
            missing.append(
                MissingInfo(
                    item=f"supuesto {aid} ({what})",
                    why_it_matters="Sin este coeficiente no se puede calcular ΔSuelo.",
                    how_to_get="Completarlo en data/assumptions.yaml con fuente o 'pendiente AFA'.",
                )
            )

    breakdown: ScoreBreakdown | None = None
    risk_pv: PValue | None = None
    if eco is not None and soil is not None:
        risk = risk_value(eco, scenarios, q, i, h, rotation.cycle_length)
        soil_term = alpha * soil.index.value
        risk_term = lam * risk
        total = math.fsum([eco.npv.value, soil_term, -risk_term])
        breakdown = ScoreBreakdown(
            npv=eco.npv,
            soil_term=PValue(
                value=soil_term,
                unit="USD/ha",
                provenance=_derived("α · ΔSuelo", "actor-profiles", "soil-impact"),
            ),
            risk_term=PValue(
                value=risk_term,
                unit="USD/ha",
                provenance=_derived("λ · Riesgo", "actor-profiles", "A-ACT-05"),
            ),
            total=PValue(
                value=total,
                unit="USD/ha",
                provenance=_derived(
                    "VAN + α·ΔSuelo − λ·Riesgo", "economics", "soil-impact", "actor-profiles"
                ),
            ),
        )
        risk_pv = PValue(
            value=risk,
            unit="USD/ha",
            provenance=_derived(
                "expected shortfall de márgenes (cola q) × AF", "economics", "A-ACT-05"
            ),
        )
        reasons += constraint_reasons(
            rotation, inp, eco.working_capital_peak.value if eco.working_capital_peak else None
        )

    risks = list(wat.risks)
    if eco is not None and eco.loss_years.count > 0:
        freq = eco.loss_years.count / eco.loss_years.total
        risks.append(
            Risk(
                risk_type=RiskType.ECONOMIC,
                severity=_level(freq, inp.resolved_assumptions),
                description=f"Margen bruto negativo en {eco.loss_years.count} de {eco.loss_years.total} años del registro.",
                basis="EVIDENCE",
                reference="economics:annual_margins",
            )
        )
    benefits: list[Benefit] = []
    if soil is not None:
        for comp in soil.components:
            if comp.contribution.value > 0:
                benefits.append(
                    Benefit(description=_COMPONENT_LABELS[comp.name], value=comp.contribution)
                )
    evidence = list(wat.evidence) + (list(soil.evidence) if soil else [])
    if soil is not None:
        missing += list(soil.missing)

    return {
        "rotation": rotation,
        "is_current": is_current,
        "reasons": sorted(set(reasons), key=lambda r: r.value),
        "breakdown": breakdown,
        "risk": risk_pv,
        "soil": soil,
        "eco": eco,
        "wat": wat,
        "feasibility": feasibility,
        "adjustments": adj_rows,
        "missing": missing,
        "risks": risks,
        "benefits": benefits,
        "evidence": evidence,
    }


def _rank_key(c: dict[str, Any]) -> tuple[Any, ...]:
    b: ScoreBreakdown | None = c["breakdown"]
    eligible = not c["reasons"]
    if b is None:
        return (2, 0.0, 0.0, 0.0, c["rotation"].rotation_id)
    soil = c["soil"].index.value if c["soil"] else 0.0
    risk = c["risk"].value if c["risk"] else 0.0
    return (
        0 if eligible else 1,
        -round(b.total.value, SCORE_DIGITS),
        round(risk, SCORE_DIGITS),
        -round(soil, SCORE_DIGITS),
        c["rotation"].rotation_id,
    )


def evaluate(inp: EngineInput) -> EngineOutput:
    """Evalúa todas las candidatas, rankea y empaqueta la salida con `input_hash`."""
    warnings: list[str] = []
    scenarios = apply_year_filter(inp.scenarios, inp.year_class_filter)
    water_resolved = dict(inp.resolved_assumptions)
    if inp.year_class_filter is not YearClassFilter.ALL:
        warnings.append(f"YEAR_CLASS_FILTER_APPLIED:{inp.year_class_filter.value}")
        if not scenarios:
            warnings.append("EMPTY_YEAR_CLASS")
            scenarios = inp.scenarios
        min_years = int(_v(inp.resolved_assumptions, "A-CLI-03"))
        if len(inp.scenarios) >= min_years:
            # El mínimo de A-CLI-03 se controla sobre el conjunto completo.
            water_resolved["A-CLI-03"] = ResolvedAssumption(
                value=min(min_years, len(scenarios)), unit="años"
            )

    weights = effective_soil_weights(inp)
    candidates, current_id = build_candidates(inp)
    evaluated = [
        evaluate_candidate(r, inp, scenarios, water_resolved, weights, r.rotation_id == current_id)
        for r in candidates
    ]
    evaluated.sort(key=_rank_key)

    current = next(c for c in evaluated if c["is_current"])
    base_score = current["breakdown"].total.value if current["breakdown"] is not None else None
    results: list[RotationResult] = []
    for rank, c in enumerate(evaluated, start=1):
        b: ScoreBreakdown | None = c["breakdown"]
        delta = None
        if b is not None and base_score is not None:
            delta = PValue(
                value=0.0 if c["is_current"] else b.total.value - base_score,
                unit="USD/ha",
                provenance=_derived("puntaje menos puntaje de la actual", "rotation-engine"),
            )
        eco: EconomicsResult | None = c["eco"]
        soil: SoilImpact | None = c["soil"]
        wat: WaterAssessment = c["wat"]
        water_reasons = tuple(
            sorted(
                {r.code.value for camp in wat.campaigns for r in camp.reasons}
                | {r.code.value for r in wat.reasons}
            )
        )
        results.append(
            RotationResult(
                rotation_id=c["rotation"].rotation_id,
                name=c["rotation"].name,
                rank=rank,
                is_current=c["is_current"],
                eligible=not c["reasons"],
                exclusion_reasons=tuple(c["reasons"]),
                breakdown=b,
                soil_delta_index=soil.index if soil else None,
                risk=c["risk"],
                water_feasibility=c["feasibility"],
                water_reasons=water_reasons,
                water_adjustments=tuple(c["adjustments"]),
                score_delta_vs_current=delta,
                margin_ranges=eco.margin_ranges if eco else (),
                expected_annual_margin=eco.expected_mean if eco else None,
                annual_margins=tuple(
                    AnnualMargin(campaign_start_year=a.campaign_start_year, margin=a.margin)
                    for a in eco.annual_margins
                )
                if eco
                else (),
                loss_years=eco.loss_years if eco else None,
                worst_year_margin=eco.worst_year_margin if eco else None,
                worst_year=eco.worst_year if eco else None,
                working_capital_peak=eco.working_capital_peak if eco else None,
                rain_on_bare_soil=soil.rain_on_bare_soil if soil else None,
                bare_soil_calendar=soil.bare_soil_calendar if soil else None,
                vulnerability_calendar=wat.vulnerability,
                evidence=tuple(c["evidence"]),
                benefits=tuple(c["benefits"]),
                missing=tuple(c["missing"]),
                risks=tuple(c["risks"]),
            )
        )
    eligible = sum(1 for r in results if r.eligible)
    if eligible < MIN_OPTIONS:
        warnings.append("LOW_ELIGIBLE_COUNT")
    return EngineOutput(
        engine_version=ENGINE_VERSION,
        input_hash=inp.input_hash(),
        profile_id=inp.profile.profile_id,
        year_class_filter=inp.year_class_filter,
        years_used=tuple(sorted(s.campaign_start_year for s in scenarios)),
        effective_soil_weights=weights,
        warnings=tuple(warnings),
        results=tuple(results),
    )


def crop_label(crop: Crop) -> str:
    return CROP_INFO[crop].label_es
