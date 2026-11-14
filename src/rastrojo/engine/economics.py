"""Economía de una rotación: margen bruto por escenario, VAN con promedio de fases,
años con pérdida y capital de trabajo. Puro: los parámetros llegan en `EngineInput`."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date
from typing import Any, Literal

from rastrojo.domain.base import DomainModel
from rastrojo.domain.climate import ClimateScenario, YearClass
from rastrojo.domain.crops import CROP_INFO, Crop, CropKind, Rotation, Season
from rastrojo.domain.economics import CropEconomics, EconomicParameters, HarvestCostMode, PriceBasis
from rastrojo.domain.engine_io import ResolvedAssumption
from rastrojo.domain.provenance import DatedPValue, DerivedProvenance, PValue
from rastrojo.domain.results import LossYears, MarginRange

ECONOMICS_ASSUMPTIONS: tuple[str, ...] = (
    "A-AGR-01",
    "A-ECO-01",
    "A-ECO-02",
    "A-ECO-03",
    "A-ECO-04",
)

Adjustment = Literal["NOT_SOWN", "FORCE_DRY", "NONE"]
AdjustmentKey = tuple[Crop, int, int]  # (cultivo, posición, año)


class MissingEconomicParameterError(ValueError):
    def __init__(self, missing: tuple[tuple[str, str], ...]) -> None:
        self.missing = missing
        super().__init__(
            "faltan parámetros económicos: " + ", ".join(f"({c}, {p})" for c, p in missing)
        )


class PositionMargin(DomainModel):
    campaign_index: int
    campaign_start_year: int
    margin: PValue


class AppliedAdjustment(DomainModel):
    crop: Crop
    campaign_index: int
    campaign_start_year: int
    effect: Literal["NOT_SOWN", "FORCE_DRY"]


class EconomicsResult(DomainModel):
    rotation_id: str
    margin_matrix: tuple[PositionMargin, ...]
    annual_margins: tuple[PositionMargin, ...]  # m_s con campaign_index = -1
    expected_by_position: tuple[PValue, ...]
    expected_mean: PValue
    annuity_factor: float
    npv: PValue
    loss_years: LossYears
    worst_year_margin: PValue
    worst_year: int
    margin_ranges: tuple[MarginRange, ...]
    working_capital_peak: PValue | None
    lease_included: bool
    adjustments: tuple[AppliedAdjustment, ...]
    date_warning: str | None
    parameter_dates: tuple[date, ...]
    assumptions_used: tuple[str, ...] = ECONOMICS_ASSUMPTIONS


def _v(resolved: Mapping[str, ResolvedAssumption], aid: str) -> Any:
    return resolved[aid].value


def _derived(method: str, *inputs: str) -> DerivedProvenance:
    return DerivedProvenance(method=method, derived_from=tuple(inputs) or ("rastrojo.economics",))


def net_price(e: CropEconomics) -> float:
    assert e.price is not None and e.export_tax is not None
    if e.price_basis is PriceBasis.FOB:
        return e.price.value * (1.0 - e.export_tax.value)
    return e.price.value


def crop_margin(e: CropEconomics, year_class: YearClass) -> float:
    """MB = Y·P_net − CD − cosecha − comercialización − flete (USD/ha)."""
    assert e.direct_costs is not None and e.harvest_cost is not None
    assert e.marketing_cost is not None and e.freight is not None
    y = e.yields[year_class].value
    revenue = y * net_price(e)
    harvest = (
        e.harvest_cost.value * revenue
        if e.harvest_cost_mode is HarvestCostMode.FRACTION_OF_REVENUE
        else e.harvest_cost.value
    )
    marketing = e.marketing_cost.value * revenue
    freight = e.freight.value * y
    return math.fsum([revenue, -e.direct_costs.value, -harvest, -marketing, -freight])


def annuity_factor(i: float, h: int) -> float:
    return math.fsum((1.0 + i) ** -t for t in range(1, h + 1))


def npv_by_phases(expected: list[float], i: float, h: int) -> float:
    """Suma explícita por fases (para verificar la forma cerrada AF·Ē)."""
    L = len(expected)
    phases = [
        math.fsum(expected[(t - 1 + phi) % L] * (1.0 + i) ** -t for t in range(1, h + 1))
        for phi in range(L)
    ]
    return math.fsum(phases) / L


def _rotation_crops(rotation: Rotation) -> list[Crop]:
    return sorted(
        {c for camp in rotation.campaigns for c in (camp.winter, camp.summer) if c is not None},
        key=lambda c: c.value,
    )


def _check_missing(
    rotation: Rotation, params: EconomicParameters, resolved: Mapping[str, ResolvedAssumption]
) -> None:
    missing: list[tuple[str, str]] = []
    for crop in _rotation_crops(rotation):
        if CROP_INFO[crop].kind is CropKind.SERVICE:
            if params.service_for(crop) is None:
                missing.append((crop.value, "direct_costs"))
            continue
        e = params.for_crop(crop)
        if e is None:
            missing.append((crop.value, "all"))
            continue
        missing += [(crop.value, p) for p in e.missing_parameters()]
    if params.rent is not None and params.rent.soy_qq_ha is not None:
        soy = params.for_crop(Crop.SOY_1ST)
        if soy is None or soy.price is None or soy.export_tax is None:
            missing.append((Crop.SOY_1ST.value, "price"))
    for aid in ECONOMICS_ASSUMPTIONS:
        if aid not in resolved:
            missing.append(("assumption", aid))
    if missing:
        raise MissingEconomicParameterError(tuple(sorted(set(missing))))


def _season_class(sc: ClimateScenario, crop: Crop) -> YearClass:
    return sc.winter_class if CROP_INFO[crop].season is Season.WINTER else sc.summer_class


def _rent(params: EconomicParameters, resolved: Mapping[str, ResolvedAssumption]) -> float:
    if params.rent is None:
        return 0.0
    if params.rent.usd_ha is not None:
        return params.rent.usd_ha.value
    assert params.rent.soy_qq_ha is not None
    soy = params.for_crop(Crop.SOY_1ST)
    assert soy is not None
    t_per_qq = float(_v(resolved, "A-ECO-04"))
    return params.rent.soy_qq_ha.value * t_per_qq * net_price(soy)


def _dates(params: EconomicParameters) -> list[date]:
    out: list[date] = []
    for e in params.crops:
        for name in (
            "price",
            "export_tax",
            "direct_costs",
            "harvest_cost",
            "marketing_cost",
            "freight",
        ):
            v = getattr(e, name)
            if isinstance(v, DatedPValue):
                out.append(v.reference_date)
        out += [y.reference_date for y in e.yields.values()]
    out += [s.direct_costs.reference_date for s in params.service_crops]
    if params.rent is not None:
        for v in (params.rent.usd_ha, params.rent.soy_qq_ha):
            if v is not None:
                out.append(v.reference_date)
    return out


def _month(spec: str) -> int:
    raw = str(spec)
    if raw.startswith("+1-"):
        raw = raw[3:]
    return int(raw.split("-")[0])


def working_capital_peak(
    rotation: Rotation,
    params: EconomicParameters,
    scenarios: tuple[ClimateScenario, ...],
    resolved: Mapping[str, ResolvedAssumption],
    rent: float,
) -> float:
    """Pico de necesidad acumulada (egresos − ingresos esperados) por posición; máximo del ciclo."""
    cal = dict(_v(resolved, "A-AGR-01"))
    schedule = dict(dict(_v(resolved, "A-ECO-01"))["DEFAULT"])
    lag = int(_v(resolved, "A-ECO-02"))
    eco3 = dict(_v(resolved, "A-ECO-03"))
    start, rent_month = int(eco3["campaign_start_month"]), int(eco3["rent_payment_month"])

    def idx(month: int) -> int:
        return (month - start) % 12

    peaks: list[float] = []
    for camp in rotation.campaigns:
        out = [0.0] * 12
        inc = [0.0] * 12
        out[idx(rent_month)] += rent
        for crop in (camp.winter, camp.summer):
            if crop is None:
                continue
            sow_m = _month(cal[crop.value]["sow"])
            harv_m = _month(cal[crop.value]["harvest"])
            if CROP_INFO[crop].kind is CropKind.SERVICE:
                svc = params.service_for(crop)
                assert svc is not None
                cd = svc.direct_costs.value
                for off, frac in schedule.items():
                    out[idx(sow_m + int(off))] += cd * float(frac)
                continue
            e = params.for_crop(crop)
            assert e is not None and e.direct_costs is not None
            for off, frac in schedule.items():
                out[idx(sow_m + int(off))] += e.direct_costs.value * float(frac)
            exp_rev = math.fsum(
                sc.weight * e.yields[_season_class(sc, crop)].value * net_price(e)
                for sc in scenarios
            )
            exp_margin = math.fsum(
                sc.weight * crop_margin(e, _season_class(sc, crop)) for sc in scenarios
            )
            harvest_costs = exp_rev - e.direct_costs.value - exp_margin
            out[idx(harv_m)] += harvest_costs
            pay_idx = idx(harv_m) + lag
            if pay_idx < 12:  # un cobro posterior al año de campaña no financia sus egresos
                inc[pay_idx] += exp_rev
        cum_out = cum_in = 0.0
        need = 0.0
        for m in range(12):
            cum_out += out[m]
            cum_in += inc[m]
            need = max(need, cum_out - cum_in)
        peaks.append(need)
    return max(peaks) if peaks else 0.0


def evaluate_economics(
    rotation: Rotation,
    params: EconomicParameters,
    scenarios: tuple[ClimateScenario, ...],
    horizon: int,
    discount_rate: float,
    resolved: Mapping[str, ResolvedAssumption],
    adjustments: Mapping[AdjustmentKey, Adjustment] | None = None,
) -> EconomicsResult:
    _check_missing(rotation, params, resolved)
    adjustments = adjustments or {}
    ordered = sorted(scenarios, key=lambda s: s.campaign_start_year)
    rent = _rent(params, resolved)
    lease = params.rent is not None
    L = rotation.cycle_length
    prov = _derived(
        "margen bruto de campaña (rinde × precio neto − costos)", "economics", "climate-scenarios"
    )

    matrix: list[PositionMargin] = []
    applied: list[AppliedAdjustment] = []
    m_by_pos_year: dict[tuple[int, int], float] = {}
    for p, camp in enumerate(rotation.campaigns):
        for sc in ordered:
            y = sc.campaign_start_year
            parts: list[float] = []
            for crop in (camp.winter, camp.summer):
                if crop is None:
                    continue
                adj = adjustments.get((crop, p, y), "NONE")
                if adj == "NOT_SOWN":
                    applied.append(
                        AppliedAdjustment(
                            crop=crop, campaign_index=p, campaign_start_year=y, effect="NOT_SOWN"
                        )
                    )
                    continue
                if CROP_INFO[crop].kind is CropKind.SERVICE:
                    svc = params.service_for(crop)
                    assert svc is not None
                    parts.append(-svc.direct_costs.value)
                    continue
                e = params.for_crop(crop)
                assert e is not None
                cls = _season_class(sc, crop)
                if adj == "FORCE_DRY":
                    cls = YearClass.DRY
                    applied.append(
                        AppliedAdjustment(
                            crop=crop, campaign_index=p, campaign_start_year=y, effect="FORCE_DRY"
                        )
                    )
                parts.append(crop_margin(e, cls))
            parts.append(-rent)
            m = math.fsum(parts)
            m_by_pos_year[(p, y)] = m
            matrix.append(
                PositionMargin(
                    campaign_index=p,
                    campaign_start_year=y,
                    margin=PValue(value=round(m, 6), unit="USD/ha", provenance=prov),
                )
            )

    expected = [
        math.fsum(sc.weight * m_by_pos_year[(p, sc.campaign_start_year)] for sc in ordered)
        for p in range(L)
    ]
    mean = math.fsum(expected) / L
    af = annuity_factor(discount_rate, horizon)
    npv = af * mean

    annual = {
        sc.campaign_start_year: math.fsum(
            m_by_pos_year[(p, sc.campaign_start_year)] for p in range(L)
        )
        / L
        for sc in ordered
    }
    annual_rows = tuple(
        PositionMargin(
            campaign_index=-1,
            campaign_start_year=y,
            margin=PValue(
                value=round(v, 6),
                unit="USD/ha",
                provenance=_derived("margen anual promedio sobre posiciones (m_s)", "economics"),
            ),
        )
        for y, v in annual.items()
    )
    loss = tuple(y for y, v in annual.items() if v < 0)
    worst_year = min(annual, key=lambda y: (annual[y], y))

    ranges: list[MarginRange] = []
    for cls in YearClass:
        rows = [
            (annual[sc.campaign_start_year], sc.weight) for sc in ordered if sc.annual_class is cls
        ]
        if not rows:
            continue
        tw = math.fsum(w for _, w in rows)
        exp = (
            math.fsum(v * w for v, w in rows) / tw
            if tw > 0
            else math.fsum(v for v, _ in rows) / len(rows)
        )
        rp = _derived(f"rango de m_s en años {cls.value}", "economics", "climate-scenarios")
        ranges.append(
            MarginRange(
                year_class=cls,
                minimum=PValue(
                    value=round(min(v for v, _ in rows), 6), unit="USD/ha", provenance=rp
                ),
                expected=PValue(value=round(exp, 6), unit="USD/ha", provenance=rp),
                maximum=PValue(
                    value=round(max(v for v, _ in rows), 6), unit="USD/ha", provenance=rp
                ),
            )
        )

    dates = sorted(set(_dates(params)))
    warning = None
    if len(dates) > 1:
        warning = (
            f"parámetros con fechas distintas: de {dates[0].isoformat()} a {dates[-1].isoformat()}"
        )

    peak = working_capital_peak(rotation, params, tuple(ordered), resolved, rent)

    return EconomicsResult(
        rotation_id=rotation.rotation_id,
        margin_matrix=tuple(matrix),
        annual_margins=annual_rows,
        expected_by_position=tuple(
            PValue(
                value=round(v, 6),
                unit="USD/ha",
                provenance=_derived("margen esperado ponderado por escenario", "economics"),
            )
            for v in expected
        ),
        expected_mean=PValue(
            value=round(mean, 6),
            unit="USD/ha",
            provenance=_derived("promedio de márgenes esperados por posición", "economics"),
        ),
        annuity_factor=round(af, 9),
        npv=PValue(
            value=round(npv, 6),
            unit="USD/ha",
            provenance=_derived(
                "VAN = AF(i, H) · Ē (promedio de fases)", "economics", "actor-profiles"
            ),
        ),
        loss_years=LossYears(count=len(loss), total=len(annual), years=loss),
        worst_year_margin=PValue(
            value=round(annual[worst_year], 6),
            unit="USD/ha",
            provenance=_derived("mínimo de m_s", "economics"),
        ),
        worst_year=worst_year,
        margin_ranges=tuple(ranges),
        working_capital_peak=PValue(
            value=round(peak, 6),
            unit="USD/ha",
            provenance=_derived(
                "pico de egresos acumulados menos ingresos esperados",
                "A-ECO-01",
                "A-ECO-02",
                "A-ECO-03",
            ),
        ),
        lease_included=lease,
        adjustments=tuple(applied),
        date_warning=warning,
        parameter_dates=tuple(dates),
    )
