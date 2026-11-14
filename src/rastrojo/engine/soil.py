"""Índice ΔSuelo por rotación y ciclo, calendario de suelo desnudo y lluvia sobre suelo desnudo.

Puro y determinista. Coeficientes de A-SOIL-01..11 y calendario A-AGR-01 resueltos en la
entrada. NDVI solo como evidencia de la rotación actual, nunca como entrada del índice.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal

from rastrojo.domain.base import DomainModel
from rastrojo.domain.climate import ClimateScenario, WaterInputs
from rastrojo.domain.crops import CROP_INFO, Crop, CropKind, Rotation
from rastrojo.domain.engine_io import ResolvedAssumption
from rastrojo.domain.provenance import Dataset, DerivedProvenance, Period, PValue
from rastrojo.domain.results import BareSoilCalendar, Evidence, MissingInfo

SOIL_ASSUMPTIONS: tuple[str, ...] = (
    "A-AGR-01",
    "A-CLI-01",
    "A-SOIL-01",
    "A-SOIL-02",
    "A-SOIL-03",
    "A-SOIL-04",
    "A-SOIL-05",
    "A-SOIL-06",
    "A-SOIL-07",
    "A-SOIL-08",
    "A-SOIL-09",
    "A-SOIL-10",
    "A-SOIL-11",
    "A-WAT-09",
)
COMPONENTS: tuple[str, ...] = ("cover", "carbon", "nitrogen", "weeds", "roots")
CYCLE_DAYS = 365
_REF_YEAR = 2001  # año no bisiesto para ubicar meses en el ciclo de 365 días
WEIGHT_TOL = 1e-9

ComponentName = Literal["cover", "carbon", "nitrogen", "weeds", "roots"]


class MissingSoilAssumptionError(ValueError):
    def __init__(self, missing: list[tuple[str, str]]) -> None:
        self.missing = missing
        detail = ", ".join(f"{aid} ({what})" for aid, what in missing)
        super().__init__(f"faltan supuestos de suelo: {detail}")


class InvalidSoilAssumptionError(ValueError):
    """Pesos que no suman 1 o coeficientes fuera de dominio."""


@dataclass(frozen=True)
class SoilConfig:
    weights: dict[str, float]
    persistence: dict[Crop, int]
    cover_ref: float
    cover_scale: float
    carbon: dict[Crop, float]
    carbon_ref: float
    carbon_scale: float
    nitrogen: dict[Crop, float]
    nitrogen_scale: float
    d_max: int
    beta: float
    roots: dict[Crop, float]
    ndvi_threshold: float
    ndvi_tolerance: float
    sow: dict[Crop, tuple[int, int, int]]
    harvest: dict[Crop, tuple[int, int, int]]
    campaign_start: tuple[int, int]
    cover_termination_days: int | None


def _md(text: str) -> tuple[int, int, int]:
    raw = str(text)
    off = 0
    if raw.startswith("+1-"):
        off, raw = 1, raw[3:]
    m, d = (int(x) for x in raw.split("-"))
    return off, m, d


def soil_config(
    resolved: dict[str, ResolvedAssumption],
    crops: set[Crop],
    effective_weights: dict[str, float] | None = None,
) -> SoilConfig:
    missing: list[tuple[str, str]] = []

    def get(aid: str) -> Any:
        if aid not in resolved:
            missing.append((aid, "registro completo"))
            return None
        return resolved[aid].value

    raw = {aid: get(aid) for aid in SOIL_ASSUMPTIONS if aid not in ("A-CLI-01", "A-WAT-09")}
    cli = get("A-CLI-01")
    if missing:
        raise MissingSoilAssumptionError(missing)

    def per_crop(aid: str, kind: type) -> dict[Crop, Any]:
        table = dict(raw[aid])
        out: dict[Crop, Any] = {}
        for c in sorted(crops, key=lambda x: x.value):
            if c.value not in table:
                missing.append((aid, c.value))
            else:
                out[c] = kind(table[c.value])
        return out

    persistence = per_crop("A-SOIL-02", int)
    carbon = per_crop("A-SOIL-04", float)
    nitrogen = per_crop("A-SOIL-06", float)
    roots = per_crop("A-SOIL-09", float)
    cal = dict(raw["A-AGR-01"])
    sow: dict[Crop, tuple[int, int, int]] = {}
    harvest: dict[Crop, tuple[int, int, int]] = {}
    for c in crops:
        if c.value not in cal:
            missing.append(("A-AGR-01", c.value))
        else:
            sow[c] = _md(cal[c.value]["sow"])
            harvest[c] = _md(cal[c.value]["harvest"])
    if missing:
        raise MissingSoilAssumptionError(missing)

    weights = (
        dict(effective_weights)
        if effective_weights is not None
        else {k: float(v) for k, v in dict(raw["A-SOIL-01"]).items()}
    )
    if set(weights) != set(COMPONENTS):
        raise InvalidSoilAssumptionError(f"los pesos deben cubrir {COMPONENTS}")
    if any(w < 0 for w in weights.values()) or abs(math.fsum(weights.values()) - 1) > WEIGHT_TOL:
        raise InvalidSoilAssumptionError("los pesos de ΔSuelo deben ser >= 0 y sumar 1")
    if any(v < 0 for v in carbon.values()):
        raise InvalidSoilAssumptionError("el aporte de carbono no puede ser negativo (A-SOIL-04)")
    if any(not (0 <= v <= 1) for v in roots.values()):
        raise InvalidSoilAssumptionError("el efecto radicular debe estar en [0, 1] (A-SOIL-09)")
    cov = dict(raw["A-SOIL-03"])
    carb = dict(raw["A-SOIL-05"])
    weed = dict(raw["A-SOIL-08"])
    start = _md(dict(cli)["winter"]["start"])
    term = resolved.get("A-WAT-09")
    return SoilConfig(
        weights=weights,
        persistence=persistence,
        cover_ref=float(cov["ref"]),
        cover_scale=float(cov["scale"]),
        carbon=carbon,
        carbon_ref=float(carb["ref"]),
        carbon_scale=float(carb["scale"]),
        nitrogen=nitrogen,
        nitrogen_scale=float(raw["A-SOIL-07"]),
        d_max=int(weed["d_max"]),
        beta=float(weed["beta"]),
        roots=roots,
        ndvi_threshold=float(raw["A-SOIL-10"]),
        ndvi_tolerance=float(raw["A-SOIL-11"]),
        sow=sow,
        harvest=harvest,
        campaign_start=(start[1], start[2]),
        cover_termination_days=int(term.value) if term is not None else None,  # type: ignore[arg-type]
    )


class SoilComponent(DomainModel):
    name: ComponentName
    raw: PValue
    score: float
    weight: float
    contribution: PValue


class CampaignContribution(DomainModel):
    campaign_index: int
    points: PValue


class SoilImpact(DomainModel):
    rotation_id: str
    index: PValue
    components: tuple[SoilComponent, ...]
    by_campaign: tuple[CampaignContribution, ...]
    bare_soil_calendar: BareSoilCalendar
    no_live_crop_days_by_month: tuple[float, ...]
    rain_on_bare_soil: PValue
    rain_on_bare_soil_by_month: tuple[float, ...]
    observed_bare_months: tuple[bool, ...] | None = None
    evidence: tuple[Evidence, ...] = ()
    missing: tuple[MissingInfo, ...] = ()
    assumptions_used: tuple[str, ...] = SOIL_ASSUMPTIONS


def _clamp(x: float) -> float:
    return max(-1.0, min(1.0, x))


def _offset(cfg: SoilConfig, spec: tuple[int, int, int]) -> int:
    start = date(_REF_YEAR, cfg.campaign_start[0], cfg.campaign_start[1])
    d = date(_REF_YEAR + spec[0], spec[1], spec[2])
    return (d - start).days


def _intervals(
    rotation: Rotation, cfg: SoilConfig, with_residue: bool
) -> list[tuple[int, int, int]]:
    """Intervalos [inicio, fin) en días absolutos del ciclo de L·365 (antes de envolver)."""
    out: list[tuple[int, int, int]] = []
    for p, camp in enumerate(rotation.campaigns):
        base = p * CYCLE_DAYS
        summer_start: int | None = None
        if camp.summer is not None:
            summer_start = _offset(cfg, cfg.sow[camp.summer])
        for crop in (camp.winter, camp.summer):
            if crop is None:
                continue
            s = _offset(cfg, cfg.sow[crop])
            e = _offset(cfg, cfg.harvest[crop])
            if (
                CROP_INFO[crop].kind is CropKind.SERVICE
                and summer_start is not None
                and cfg.cover_termination_days is not None
            ):
                e = summer_start - cfg.cover_termination_days
            if with_residue:
                e += cfg.persistence[crop]
            out.append((p, base + s, base + e + 1))
    return out


def _covered_mask(rotation: Rotation, cfg: SoilConfig, with_residue: bool) -> list[bool]:
    total = rotation.cycle_length * CYCLE_DAYS
    mask = [False] * total
    for _, s, e in _intervals(rotation, cfg, with_residue):
        for d in range(s, e):
            mask[d % total] = True
    return mask


def _month_of_cycle_day(cfg: SoilConfig, day: int) -> int:
    start = date(_REF_YEAR, cfg.campaign_start[0], cfg.campaign_start[1])
    return (start + timedelta(days=day % CYCLE_DAYS)).month


def _derived(method: str, *inputs: str) -> DerivedProvenance:
    return DerivedProvenance(method=method, derived_from=tuple(inputs))


def evaluate_soil(
    rotation: Rotation,
    resolved: dict[str, ResolvedAssumption],
    scenarios: tuple[ClimateScenario, ...] = (),
    inputs: WaterInputs | None = None,
    effective_weights: dict[str, float] | None = None,
    is_current: bool = False,
) -> SoilImpact:
    crops = {c for camp in rotation.campaigns for c in (camp.winter, camp.summer) if c is not None}
    cfg = soil_config(resolved, crops, effective_weights)
    L = rotation.cycle_length

    covered = _covered_mask(rotation, cfg, with_residue=True)
    live = _covered_mask(rotation, cfg, with_residue=False)
    cov_by_campaign = [
        sum(covered[p * CYCLE_DAYS : (p + 1) * CYCLE_DAYS]) / CYCLE_DAYS for p in range(L)
    ]
    x_cov = math.fsum(cov_by_campaign) / L

    carb_by_campaign = [
        math.fsum(cfg.carbon[c] for c in (camp.winter, camp.summer) if c is not None)
        for camp in rotation.campaigns
    ]
    x_carb = math.fsum(carb_by_campaign) / L
    n_by_campaign = [
        math.fsum(cfg.nitrogen[c] for c in (camp.winter, camp.summer) if c is not None)
        for camp in rotation.campaigns
    ]
    x_n = math.fsum(n_by_campaign) / L

    species = {_species(c) for c in crops}
    d = len(species)
    f_w = sum(1 for camp in rotation.campaigns if camp.winter is not None) / L
    x_weed = cfg.beta * min(1.0, (d - 1) / (cfg.d_max - 1)) + (1 - cfg.beta) * f_w
    root_by_campaign = [
        min(1.0, math.fsum(cfg.roots[c] for c in (camp.winter, camp.summer) if c is not None))
        for camp in rotation.campaigns
    ]
    x_root = math.fsum(root_by_campaign) / L

    scores = {
        "cover": _clamp((x_cov - cfg.cover_ref) / cfg.cover_scale),
        "carbon": _clamp((x_carb - cfg.carbon_ref) / cfg.carbon_scale),
        "nitrogen": _clamp(x_n / cfg.nitrogen_scale),
        "weeds": 2 * x_weed - 1,
        "roots": 2 * x_root - 1,
    }
    raws = {
        "cover": (x_cov, "fraction", ("A-AGR-01", "A-SOIL-02")),
        "carbon": (x_carb, "index", ("A-SOIL-04",)),
        "nitrogen": (x_n, "index", ("A-SOIL-06",)),
        "weeds": (x_weed, "fraction", ("A-SOIL-08",)),
        "roots": (x_root, "fraction", ("A-SOIL-09",)),
    }
    components: list[SoilComponent] = []
    contribs: dict[str, float] = {}
    for k in COMPONENTS:
        value, unit, ids = raws[k]
        contribution = 100.0 * cfg.weights[k] * scores[k]
        contribs[k] = contribution
        components.append(
            SoilComponent(
                name=k,
                raw=PValue(
                    value=round(value, 6),
                    unit=unit,
                    provenance=_derived(f"componente {k} del índice ΔSuelo", *ids),
                ),
                score=round(scores[k], 6),
                weight=cfg.weights[k],
                contribution=PValue(
                    value=round(contribution, 6),
                    unit="index",
                    provenance=_derived("100 · w_k · s_k", "A-SOIL-01", *ids),
                ),
            )
        )
    total = math.fsum(contribs.values())
    index = PValue(
        value=round(total, 6),
        unit="index",
        provenance=_derived("ΔSuelo = 100 · Σ w_k · s_k", "A-SOIL-01"),
    )

    # Reparto por campaña: proporcional al aporte bruto de cada componente lineal; malezas en partes iguales.
    per_campaign = [0.0] * L
    shares = {
        "cover": cov_by_campaign,
        "carbon": carb_by_campaign,
        "nitrogen": n_by_campaign,
        "roots": root_by_campaign,
    }
    for k in COMPONENTS:
        if k == "weeds":
            for p in range(L):
                per_campaign[p] += contribs[k] / L
            continue
        vals = shares[k]
        denom = math.fsum(abs(v) for v in vals)
        for p in range(L):
            per_campaign[p] += contribs[k] * (abs(vals[p]) / denom if denom > 0 else 1.0 / L)
    by_campaign = tuple(
        CampaignContribution(
            campaign_index=p,
            points=PValue(
                value=round(v, 6),
                unit="index",
                provenance=_derived("reparto del índice por campaña", "A-SOIL-01"),
            ),
        )
        for p, v in enumerate(per_campaign)
    )

    uncovered_days = [0.0] * 12
    no_live_days = [0.0] * 12
    for day in range(L * CYCLE_DAYS):
        m = _month_of_cycle_day(cfg, day) - 1
        if not covered[day]:
            uncovered_days[m] += 1
        if not live[day]:
            no_live_days[m] += 1
    uncovered_days = [round(v / L, 6) for v in uncovered_days]
    no_live_days = [round(v / L, 6) for v in no_live_days]
    calendar = BareSoilCalendar(
        days_by_month=tuple(uncovered_days),
        provenance=_derived(
            "días sin cultivo vivo ni rastrojo por mes, promedio del ciclo", "A-AGR-01", "A-SOIL-02"
        ),
    )

    rain_total, rain_month = _rain_on_bare(covered, L, cfg, scenarios, inputs)
    missing: list[MissingInfo] = []
    evidence: list[Evidence] = []
    observed: tuple[bool, ...] | None = None
    if is_current:
        observed, ev, miss = _ndvi_evidence(inputs, cfg, uncovered_days)
        evidence += ev
        missing += miss

    return SoilImpact(
        rotation_id=rotation.rotation_id,
        index=index,
        components=tuple(components),
        by_campaign=by_campaign,
        bare_soil_calendar=calendar,
        no_live_crop_days_by_month=tuple(no_live_days),
        rain_on_bare_soil=PValue(
            value=round(rain_total, 6),
            unit="mm",
            provenance=_derived(
                "lluvia POWER en días sin cultivo vivo ni rastrojo, media ponderada por escenario",
                "NASA_POWER:PRECTOTCORR",
                "A-AGR-01",
                "A-SOIL-02",
            ),
        ),
        rain_on_bare_soil_by_month=tuple(round(v, 6) for v in rain_month),
        observed_bare_months=observed,
        evidence=tuple(evidence),
        missing=tuple(missing),
    )


def _species(crop: Crop) -> str:
    return {
        Crop.SOY_1ST: "soy",
        Crop.SOY_2ND: "soy",
        Crop.MAIZE_EARLY: "maize",
        Crop.MAIZE_LATE: "maize",
        Crop.WHEAT: "wheat",
        Crop.COVER_VETCH: "vetch",
        Crop.COVER_RYE: "rye",
        Crop.COVER_OAT: "oat",
    }[crop]


def _rain_on_bare(
    covered: list[bool],
    L: int,
    cfg: SoilConfig,
    scenarios: tuple[ClimateScenario, ...],
    inputs: WaterInputs | None,
) -> tuple[float, list[float]]:
    if inputs is None or not scenarios:
        return 0.0, [0.0] * 12
    by_year = {w.campaign_start_year: w for w in inputs.weather}
    totals: list[tuple[float, float]] = []
    months: list[tuple[list[float], float]] = []
    for sc in sorted(scenarios, key=lambda s: s.campaign_start_year):
        w = by_year.get(sc.campaign_start_year)
        if w is None:
            continue
        start = date(sc.campaign_start_year, cfg.campaign_start[0], cfg.campaign_start[1])
        offset = (start - w.start_date).days
        if offset < 0 or offset + CYCLE_DAYS > len(w.rain_mm):
            continue
        per_month = [0.0] * 12
        values: list[float] = []
        for p in range(L):
            for day in range(CYCLE_DAYS):
                if not covered[p * CYCLE_DAYS + day]:
                    r = w.rain_mm[offset + day]
                    values.append(r)
                    per_month[(start + timedelta(days=day)).month - 1] += r
        totals.append((math.fsum(values) / L, sc.weight))
        months.append(([v / L for v in per_month], sc.weight))
    total_w = math.fsum(wt for _, wt in totals)
    if total_w <= 0:
        return 0.0, [0.0] * 12
    total = math.fsum(v * wt for v, wt in totals) / total_w
    by_month = [math.fsum(m[i] * wt for m, wt in months) / total_w for i in range(12)]
    return total, by_month


def _ndvi_evidence(
    inputs: WaterInputs | None, cfg: SoilConfig, uncovered_days: list[float]
) -> tuple[tuple[bool, ...] | None, list[Evidence], list[MissingInfo]]:
    if inputs is None or inputs.ndvi_monthly is None:
        return (
            None,
            [],
            [
                MissingInfo(
                    item="NDVI histórico del lote",
                    why_it_matters="Permite contrastar la cobertura modelada de la rotación actual con lo que ve el satélite.",
                    how_to_get="Bajar MODIS MOD13Q1 o HLS para el lote y resumir por mes.",
                )
            ],
        )
    observed = tuple(v.value < cfg.ndvi_threshold for v in inputs.ndvi_monthly)
    modeled = tuple(d > 15 for d in uncovered_days)
    mismatch = sum(1 for a, b in zip(observed, modeled, strict=True) if a != b) / 12
    first = inputs.ndvi_monthly[0]
    period = Period(start=date(2000, 1, 1), end=date(2025, 12, 31))
    if hasattr(first.provenance, "source"):
        period = first.provenance.source.period
    bare_months = sum(observed)
    evidence = [
        Evidence(
            dataset=Dataset.MODIS_NDVI,
            variable="NDVI mensual del lote",
            period=period,
            value=PValue(
                value=bare_months,
                unit="count",
                provenance=_derived("meses con NDVI < umbral A-SOIL-10", "MODIS_NDVI", "A-SOIL-10"),
            ),
            interpretation="Meses del año en que el satélite ve el lote con poca vegetación en la rotación actual.",
        )
    ]
    missing: list[MissingInfo] = []
    if mismatch > cfg.ndvi_tolerance:
        missing.append(
            MissingInfo(
                item="calendario real de siembras y cosechas del lote",
                why_it_matters="La cobertura modelada no coincide con la que ve el satélite; las fechas del lote pueden ser otras.",
                how_to_get="Pedirle al productor o al agrónomo las fechas reales de la rotación actual.",
            )
        )
    return observed, evidence, missing
