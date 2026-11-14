"""Procedencia de cada número: fuentes, supuestos y valores con unidad."""

from __future__ import annotations

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, JsonValue, model_validator

from rastrojo.domain.base import DomainModel


class Dataset(StrEnum):
    NASA_POWER = "NASA_POWER"
    SMAP_L4 = "SMAP_L4"
    GPM_IMERG = "GPM_IMERG"
    GRACE_FO = "GRACE_FO"
    MODIS_NDVI = "MODIS_NDVI"
    HLS_NDVI = "HLS_NDVI"
    SOILGRIDS = "SOILGRIDS"
    GLDAS = "GLDAS"
    SRTM = "SRTM"
    ECOSTRESS = "ECOSTRESS"
    FIELD_HAMMER = "FIELD_HAMMER"


ASSUMPTION_AREAS: tuple[str, ...] = ("AGR", "CLI", "WAT", "SOIL", "ECO", "ACT", "FLD", "DEMO")
_ASSUMPTION_RE = re.compile(r"^A-([A-Z]+)-(\d{2})$")


def _check_assumption_id(value: str) -> str:
    match = _ASSUMPTION_RE.fullmatch(value)
    if match is None:
        raise ValueError(
            f"assumption_id '{value}' no cumple el formato A-<AREA>-<NN> (ejemplo: A-WAT-01)"
        )
    area = match.group(1)
    if area not in ASSUMPTION_AREAS:
        raise ValueError(
            f"área de supuesto '{area}' desconocida; "
            f"áreas permitidas: {', '.join(ASSUMPTION_AREAS)}"
        )
    return value


AssumptionId = Annotated[str, AfterValidator(_check_assumption_id)]


class Period(DomainModel):
    start: date
    end: date

    @model_validator(mode="after")
    def _ordered(self) -> Period:
        if self.end < self.start:
            raise ValueError("el período termina antes de empezar")
        return self


class Source(DomainModel):
    """De dónde sale un dato publicado por un tercero (o medido en campo)."""

    dataset: Dataset
    variable: str = Field(min_length=1)
    period: Period
    spatial_resolution: str = Field(min_length=1, description="Ej.: '~9 km', '0.5° x 0.625°'")
    temporal_resolution: str = Field(min_length=1, description="Ej.: 'diaria', '3-horaria'")
    is_modeled: bool = Field(description="True si el producto sale de un modelo o reanálisis")
    location_note: str | None = Field(
        default=None, description="Celda efectiva o punto muestreado, si aplica"
    )


class AssumptionStatus(StrEnum):
    PENDING_AFA = "PENDING_AFA"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class Assumption(DomainModel):
    """Entrada del registro de supuestos (docs/assumptions.md)."""

    assumption_id: AssumptionId
    description: str = Field(min_length=1)
    value: JsonValue
    unit: str | None = None
    reference: str = Field(min_length=1, description="Fuente bibliográfica o 'pendiente AFA'")
    status: AssumptionStatus


class ObservedProvenance(DomainModel):
    kind: Literal["OBSERVED"] = "OBSERVED"
    source: Source


class DerivedProvenance(DomainModel):
    kind: Literal["DERIVED"] = "DERIVED"
    method: str = Field(min_length=1)
    derived_from: tuple[str, ...] = Field(min_length=1, description="Ids de los insumos")


class AssumptionProvenance(DomainModel):
    kind: Literal["ASSUMPTION"] = "ASSUMPTION"
    assumption_id: AssumptionId


class UserInputProvenance(DomainModel):
    kind: Literal["USER_INPUT"] = "USER_INPUT"
    note: str | None = None


Provenance = Annotated[
    ObservedProvenance | DerivedProvenance | AssumptionProvenance | UserInputProvenance,
    Field(discriminator="kind"),
]

Unit = Literal[
    "mm",
    "mm/day",
    "degC",
    "m3/m3",
    "USD/ha",
    "USD/t",
    "USD/ha/point",
    "t/ha",
    "qq/ha",
    "%",
    "fraction",
    "ratio",
    "ha",
    "m",
    "days",
    "year",
    "index",
    "count",
    "MJ/m2/day",
    "m/s",
]


class PValue(DomainModel):
    """Valor con unidad y procedencia. Todo número que cruza capas viaja así."""

    value: float
    unit: Unit
    provenance: Provenance


class DatedPValue(PValue):
    """Parámetro económico: además de procedencia, lleva su fecha de referencia."""

    reference_date: date
