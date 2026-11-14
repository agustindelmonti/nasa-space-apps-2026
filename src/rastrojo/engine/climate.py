"""Clasificación determinista de años históricos (seco / normal / húmedo).

Función pura: sin I/O, red, reloj ni azar. Los valores de A-CLI-01..03 llegan en la
configuración, resueltos por la capa de aplicación.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from rastrojo.domain.base import DomainModel
from rastrojo.domain.climate import ClimateScenario, YearClass
from rastrojo.domain.provenance import (
    Dataset,
    DerivedProvenance,
    PValue,
    Source,
)

RAIN_ROUND_DIGITS = 1  # comparar lluvias redondeadas a 0,1 mm (decisión 2)
_NOISE_DIGITS = 6


def round_rain(value: float) -> float:
    """Redondeo a 0,1 mm mitad hacia arriba, después de descartar ruido de punto flotante."""
    clean = Decimal(f"{round(value, _NOISE_DIGITS):.{_NOISE_DIGITS}f}")
    return float(clean.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


WindowName = Literal["WINTER", "SUMMER"]


class ClimateErrorCode(StrEnum):
    MIXED_SOURCES = "MIXED_SOURCES"
    INSUFFICIENT_YEARS = "INSUFFICIENT_YEARS"


class ClimateClassificationError(ValueError):
    def __init__(self, code: ClimateErrorCode, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


class WindowDef(DomainModel):
    """Ventana de una campaña. Si el mes de fin es anterior al de inicio, cruza el año."""

    name: WindowName
    start_month: int = Field(ge=1, le=12)
    start_day: int = Field(ge=1, le=31)
    end_month: int = Field(ge=1, le=12)
    end_day: int = Field(ge=1, le=31)
    crosses_year: bool = Field(
        default=False, description="True si la ventana termina en el año calendario siguiente"
    )
    starts_next_year: bool = Field(
        default=False, description="True si la ventana empieza el año calendario siguiente"
    )

    @model_validator(mode="after")
    def _valid_dates(self) -> WindowDef:
        # Validar con un año bisiesto para admitir 29/2.
        start = date(2000, self.start_month, self.start_day)
        end = date(2000, self.end_month, self.end_day)
        if not self.crosses_year and end < start:
            raise ValueError("la ventana termina antes de empezar")
        if self.crosses_year and end >= start:
            raise ValueError(
                "una ventana que cruza el año debe terminar antes de su fecha de inicio"
            )
        return self

    def bounds(self, campaign_year: int) -> tuple[date, date]:
        y0 = campaign_year + (1 if self.starts_next_year else 0)
        start = date(y0, self.start_month, self.start_day)
        y1 = y0 + (1 if self.crosses_year else 0)
        return start, date(y1, self.end_month, self.end_day)


class ClassificationConfig(DomainModel):
    winter: WindowDef
    summer: WindowDef
    max_missing_days: int = Field(ge=0)
    min_years: int = Field(ge=3)
    assumption_ids: tuple[str, ...] = ("A-CLI-01", "A-CLI-02", "A-CLI-03")

    @model_validator(mode="after")
    def _names(self) -> ClassificationConfig:
        if self.winter.name != "WINTER" or self.summer.name != "SUMMER":
            raise ValueError("las ventanas deben llamarse WINTER y SUMMER")
        return self


class RainDay(DomainModel):
    day: date
    mm: float | None = Field(default=None, ge=0)
    dataset: Dataset


class RainSeries(DomainModel):
    """Serie diaria de lluvia. Un día ausente o con `mm=None` es un hueco explícito."""

    source: Source
    days: tuple[RainDay, ...] = Field(min_length=1)


class ExclusionReason(StrEnum):
    MISSING_DAYS = "MISSING_DAYS"
    INCOMPLETE_WINDOW = "INCOMPLETE_WINDOW"


class Exclusion(DomainModel):
    campaign_year: int
    window: Literal["WINTER", "SUMMER", "CAMPAIGN"]
    reason: ExclusionReason
    missing_days: int = Field(ge=0)


class TieBreak(DomainModel):
    years: tuple[int, ...]
    rain_mm: float
    boundary: Literal["DRY_NORMAL", "NORMAL_WET"]


class YearClassification(DomainModel):
    campaign_year: int
    rain: PValue
    year_class: YearClass


class ClassificationResult(DomainModel):
    window: Literal["WINTER", "SUMMER", "CAMPAIGN"]
    years: tuple[YearClassification, ...]
    lower_bound: PValue
    upper_bound: PValue
    exclusions: tuple[Exclusion, ...]
    tie_breaks: tuple[TieBreak, ...]
    weight: float
    class_frequency: dict[YearClass, float]
    assumption_ids: tuple[str, ...]


class CombinedScenarios(DomainModel):
    scenarios: tuple[ClimateScenario, ...]
    winter: ClassificationResult
    summer: ClassificationResult
    annual: ClassificationResult
    exclusions: tuple[Exclusion, ...]


def _check_single_source(series: RainSeries) -> None:
    datasets = {d.dataset for d in series.days} | {series.source.dataset}
    if len(datasets) > 1:
        names = ", ".join(sorted(ds.value for ds in datasets))
        raise ClimateClassificationError(
            ClimateErrorCode.MIXED_SOURCES, f"la serie mezcla fuentes: {names}"
        )


def _window_total(
    by_day: dict[date, float | None], first: date, last: date, start: date, end: date
) -> tuple[float | None, int, bool]:
    """Devuelve (acumulado, días faltantes, ventana_completa_en_la_serie)."""
    if start < first or end > last:
        return None, 0, False
    values: list[float] = []
    missing = 0
    current = start
    while current <= end:
        v = by_day.get(current)
        if v is None:
            missing += 1
        else:
            values.append(v)
        current += timedelta(days=1)
    return math.fsum(values), missing, True


def window_totals(
    series: RainSeries, window: WindowDef, max_missing: int
) -> tuple[dict[int, float], tuple[Exclusion, ...]]:
    """Acumulado por campaña de una ventana y exclusiones registradas."""
    _check_single_source(series)
    by_day = {d.day: d.mm for d in series.days}
    first, last = min(by_day), max(by_day)
    totals: dict[int, float] = {}
    exclusions: list[Exclusion] = []
    for year in range(first.year - 1, last.year + 1):
        start, end = window.bounds(year)
        if end < first or start > last:
            continue
        total, missing, complete = _window_total(by_day, first, last, start, end)
        if not complete:
            exclusions.append(
                Exclusion(
                    campaign_year=year,
                    window=window.name,
                    reason=ExclusionReason.INCOMPLETE_WINDOW,
                    missing_days=0,
                )
            )
            continue
        if missing > max_missing:
            exclusions.append(
                Exclusion(
                    campaign_year=year,
                    window=window.name,
                    reason=ExclusionReason.MISSING_DAYS,
                    missing_days=missing,
                )
            )
            continue
        assert total is not None
        totals[year] = total
    return totals, tuple(exclusions)


def _rain_pv(value: float, derived_from: tuple[str, ...]) -> PValue:
    # La suma por ventana la calcula el sistema: es DERIVED de la serie observada.
    return PValue(
        value=value,
        unit="mm",
        provenance=DerivedProvenance(
            method="suma diaria por ventana (math.fsum)", derived_from=derived_from
        ),
    )


def classify_totals(
    totals: dict[int, float],
    window: Literal["WINTER", "SUMMER", "CAMPAIGN"],
    min_years: int,
    derived_from: tuple[str, ...],
    exclusions: tuple[Exclusion, ...] = (),
    assumption_ids: tuple[str, ...] = (),
) -> ClassificationResult:
    """Terciles por rango sobre lluvia redondeada a 0,1 mm, desempate por año."""
    n = len(totals)
    if n < min_years:
        raise ClimateClassificationError(
            ClimateErrorCode.INSUFFICIENT_YEARS,
            f"{window}: {n} años válidos de {min_years} requeridos",
        )
    ordered = sorted(totals.items(), key=lambda kv: (round_rain(kv[1]), kv[0]))
    k = n // 3
    classes: dict[int, YearClass] = {}
    for pos, (year, _) in enumerate(ordered):
        if pos < k:
            classes[year] = YearClass.DRY
        elif pos >= n - k:
            classes[year] = YearClass.WET
        else:
            classes[year] = YearClass.NORMAL

    tie_breaks: list[TieBreak] = []
    for boundary, idx in (("DRY_NORMAL", k), ("NORMAL_WET", n - k)):
        if 0 < idx < n:
            below = round_rain(ordered[idx - 1][1])
            above = round_rain(ordered[idx][1])
            if below == above:
                tied = tuple(sorted(y for y, v in ordered if round_rain(v) == below))
                tie_breaks.append(TieBreak(years=tied, rain_mm=below, boundary=boundary))

    years = tuple(
        YearClassification(
            campaign_year=y,
            rain=_rain_pv(round_rain(totals[y]), derived_from),
            year_class=classes[y],
        )
        for y in sorted(totals)
    )
    bound_prov = DerivedProvenance(method="tercil por rango", derived_from=derived_from)
    lower = round_rain(ordered[k - 1][1] if k > 0 else ordered[0][1])
    upper = round_rain(ordered[n - k][1] if k > 0 else ordered[-1][1])
    counts = {c: sum(1 for v in classes.values() if v is c) for c in YearClass}
    return ClassificationResult(
        window=window,
        years=years,
        lower_bound=PValue(value=lower, unit="mm", provenance=bound_prov),
        upper_bound=PValue(value=upper, unit="mm", provenance=bound_prov),
        exclusions=exclusions,
        tie_breaks=tuple(tie_breaks),
        weight=1.0 / n,
        class_frequency={c: counts[c] / n for c in YearClass},
        assumption_ids=assumption_ids,
    )


def classify_window(
    series: RainSeries, window: WindowDef, cfg: ClassificationConfig
) -> ClassificationResult:
    totals, exclusions = window_totals(series, window, cfg.max_missing_days)
    ref = (f"{series.source.dataset.value}:{series.source.variable}",)
    return classify_totals(totals, window.name, cfg.min_years, ref, exclusions, cfg.assumption_ids)


def build_scenarios(series: RainSeries, cfg: ClassificationConfig) -> CombinedScenarios:
    """Escenarios combinados: años válidos en invierno y verano, con tres clases y pesos 1/N."""
    ref = (f"{series.source.dataset.value}:{series.source.variable}",)
    w_tot, w_exc = window_totals(series, cfg.winter, cfg.max_missing_days)
    s_tot, s_exc = window_totals(series, cfg.summer, cfg.max_missing_days)
    common = sorted(set(w_tot) & set(s_tot))
    campaign_exc = tuple(
        Exclusion(
            campaign_year=y, window="CAMPAIGN", reason=ExclusionReason.MISSING_DAYS, missing_days=0
        )
        for y in sorted((set(w_tot) | set(s_tot)) - set(common))
    )
    winter = classify_totals(
        {y: w_tot[y] for y in common}, "WINTER", cfg.min_years, ref, w_exc, cfg.assumption_ids
    )
    summer = classify_totals(
        {y: s_tot[y] for y in common}, "SUMMER", cfg.min_years, ref, s_exc, cfg.assumption_ids
    )
    campaign_totals = {y: math.fsum([w_tot[y], s_tot[y]]) for y in common}
    annual = classify_totals(
        campaign_totals, "CAMPAIGN", cfg.min_years, ref, campaign_exc, cfg.assumption_ids
    )

    w_cls = {c.campaign_year: c for c in winter.years}
    s_cls = {c.campaign_year: c for c in summer.years}
    a_cls = {c.campaign_year: c for c in annual.years}
    n = len(common)
    scenarios = tuple(
        ClimateScenario(
            campaign_start_year=y,
            annual_class=a_cls[y].year_class,
            winter_class=w_cls[y].year_class,
            summer_class=s_cls[y].year_class,
            winter_rain=w_cls[y].rain,
            summer_rain=s_cls[y].rain,
            weight=1.0 / n,
        )
        for y in common
    )
    return CombinedScenarios(
        scenarios=scenarios,
        winter=winter,
        summer=summer,
        annual=annual,
        exclusions=w_exc + s_exc + campaign_exc,
    )
