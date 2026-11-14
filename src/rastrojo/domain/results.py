"""Resultado de evaluación por rotación: puntaje, factibilidad, calendarios y evidencia."""

from __future__ import annotations

import math
from enum import StrEnum
from typing import Literal

from pydantic import Field, model_validator

from rastrojo.domain.base import DomainModel
from rastrojo.domain.climate import YearClass
from rastrojo.domain.crops import Crop
from rastrojo.domain.provenance import Dataset, DerivedProvenance, Period, PValue

SCORE_TOLERANCE = 1e-6


class WaterFeasibility(StrEnum):
    FEASIBLE = "FEASIBLE"
    RISKY = "RISKY"
    NOT_FEASIBLE = "NOT_FEASIBLE"
    UNKNOWN = "UNKNOWN"


class RiskType(StrEnum):
    WATER = "WATER"
    FROST = "FROST"
    HEAT_STRESS = "HEAT_STRESS"
    EXTREME_RAIN = "EXTREME_RAIN"
    ECONOMIC = "ECONOMIC"
    WEEDS = "WEEDS"
    SOIL = "SOIL"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ExclusionReason(StrEnum):
    DOUBLE_CROP_NOT_ALLOWED = "DOUBLE_CROP_NOT_ALLOWED"
    COVER_NOT_ALLOWED = "COVER_NOT_ALLOWED"
    WORKING_CAPITAL_EXCEEDED = "WORKING_CAPITAL_EXCEEDED"
    WATER_NEVER_FEASIBLE = "WATER_NEVER_FEASIBLE"
    MACHINERY_WINDOW_CONFLICT = "MACHINERY_WINDOW_CONFLICT"
    MISSING_PARAMETERS = "MISSING_PARAMETERS"


class Evidence(DomainModel):
    dataset: Dataset
    variable: str = Field(min_length=1)
    period: Period
    value: PValue
    interpretation: str = Field(min_length=1)


class MissingInfo(DomainModel):
    item: str = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    how_to_get: str = Field(min_length=1)


class Risk(DomainModel):
    risk_type: RiskType
    severity: Severity
    description: str = Field(min_length=1)
    basis: Literal["EVIDENCE", "ASSUMPTION"]
    reference: str = Field(min_length=1, description="Variable de evidencia o id de supuesto")


class Benefit(DomainModel):
    description: str = Field(min_length=1)
    value: PValue | None = None


class ScoreBreakdown(DomainModel):
    """score = VAN + α·ΔSuelo − λ·Riesgo (todo en USD/ha)."""

    npv: PValue
    soil_term: PValue
    risk_term: PValue
    total: PValue

    @model_validator(mode="after")
    def _consistent(self) -> ScoreBreakdown:
        for name in ("npv", "soil_term", "risk_term", "total"):
            if getattr(self, name).unit != "USD/ha":
                raise ValueError(f"{name} debe estar en 'USD/ha'")
        if self.risk_term.value < 0:
            raise ValueError("el término de riesgo es una penalidad y no puede ser negativo")
        expected = math.fsum([self.npv.value, self.soil_term.value, -self.risk_term.value])
        tol = SCORE_TOLERANCE * max(1.0, abs(expected))
        if abs(expected - self.total.value) > tol:
            raise ValueError(
                f"desglose inconsistente: VAN + suelo − riesgo = {expected} "
                f"y total = {self.total.value}"
            )
        return self


class MarginRange(DomainModel):
    year_class: YearClass
    minimum: PValue
    expected: PValue
    maximum: PValue

    @model_validator(mode="after")
    def _ordered(self) -> MarginRange:
        if not (self.minimum.value <= self.expected.value <= self.maximum.value):
            raise ValueError("el rango de margen debe cumplir mínimo ≤ esperado ≤ máximo")
        return self


class LossYears(DomainModel):
    count: int = Field(ge=0)
    total: int = Field(ge=1)
    years: tuple[int, ...]

    @model_validator(mode="after")
    def _consistent(self) -> LossYears:
        if self.count != len(self.years) or self.count > self.total:
            raise ValueError("años con pérdida inconsistentes")
        return self


class BareSoilCalendar(DomainModel):
    """Días con suelo desnudo por mes (enero a diciembre)."""

    days_by_month: tuple[float, ...] = Field(min_length=12, max_length=12)
    provenance: DerivedProvenance

    @model_validator(mode="after")
    def _range(self) -> BareSoilCalendar:
        if any(d < 0 or d > 31 for d in self.days_by_month):
            raise ValueError("los días con suelo desnudo por mes deben estar entre 0 y 31")
        return self


class VulnerabilityEntry(DomainModel):
    """Frecuencia (0 a 1) de años con el evento, por mes, para un cultivo."""

    crop: Crop
    event: Literal["FROST", "HEAT_STRESS", "WATER_DEFICIT", "EXTREME_RAIN"]
    frequency_by_month: tuple[float, ...] = Field(min_length=12, max_length=12)
    provenance: DerivedProvenance

    @model_validator(mode="after")
    def _range(self) -> VulnerabilityEntry:
        if any(f < 0 or f > 1 for f in self.frequency_by_month):
            raise ValueError("las frecuencias del calendario deben estar entre 0 y 1")
        return self


class WaterAdjustment(DomainModel):
    crop: Crop
    campaign_index: int = Field(ge=0)
    scenario_year: int
    status: WaterFeasibility
    effect: Literal["NOT_SOWN", "FORCE_DRY", "NONE"]


class RotationResult(DomainModel):
    rotation_id: str
    rank: int = Field(ge=1)
    is_current: bool
    eligible: bool
    exclusion_reasons: tuple[ExclusionReason, ...] = ()
    breakdown: ScoreBreakdown
    soil_delta_index: PValue
    water_feasibility: WaterFeasibility
    water_adjustments: tuple[WaterAdjustment, ...] = ()
    score_delta_vs_current: PValue
    margin_ranges: tuple[MarginRange, ...]
    loss_years: LossYears
    worst_year_margin: PValue
    worst_year: int
    rain_on_bare_soil: PValue
    bare_soil_calendar: BareSoilCalendar
    vulnerability_calendar: tuple[VulnerabilityEntry, ...]
    evidence: tuple[Evidence, ...]
    benefits: tuple[Benefit, ...]
    missing: tuple[MissingInfo, ...]
    risks: tuple[Risk, ...]

    @model_validator(mode="after")
    def _checks(self) -> RotationResult:
        if self.eligible and self.exclusion_reasons:
            raise ValueError("una rotación elegible no puede tener motivos de exclusión")
        if not self.eligible and not self.exclusion_reasons:
            raise ValueError("una rotación no elegible debe declarar sus motivos")
        if self.soil_delta_index.unit != "index" or not (
            -100 <= self.soil_delta_index.value <= 100
        ):
            raise ValueError("ΔSuelo debe ser un 'index' entre -100 y 100")
        if self.score_delta_vs_current.unit != "USD/ha":
            raise ValueError("score_delta_vs_current debe estar en 'USD/ha'")
        if self.is_current and self.score_delta_vs_current.value != 0:
            raise ValueError("la rotación actual tiene score_delta_vs_current = 0")
        classes = [m.year_class for m in self.margin_ranges]
        if len(set(classes)) != len(classes):
            raise ValueError("clase de año repetida en los rangos de margen")
        return self

    @property
    def score(self) -> float:
        return self.breakdown.total.value
