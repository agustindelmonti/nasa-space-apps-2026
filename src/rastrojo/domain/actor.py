"""Perfil de actor: horizonte, peso del suelo, aversión al riesgo y restricciones."""

from __future__ import annotations

from pydantic import Field, model_validator

from rastrojo.domain.base import DomainModel
from rastrojo.domain.provenance import PValue


class Constraints(DomainModel):
    allow_double_crop: bool
    allow_cover_crop: bool
    max_working_capital_usd_ha: PValue | None = Field(
        default=None, description="Ausente significa sin tope; nunca un número grande"
    )

    @model_validator(mode="after")
    def _capital(self) -> Constraints:
        cap = self.max_working_capital_usd_ha
        if cap is not None and (cap.unit != "USD/ha" or cap.value <= 0):
            raise ValueError("el capital máximo debe estar en 'USD/ha' y ser mayor a 0")
        return self


class SoilPriorities(DomainModel):
    """Pesos opcionales en [0, 1], uno por componente de ΔSuelo (ausente = 0)."""

    EROSION_COVER: float | None = Field(default=None, ge=0, le=1)
    OM_CARBON: float | None = Field(default=None, ge=0, le=1)
    NITROGEN: float | None = Field(default=None, ge=0, le=1)
    WEED_CONTROL: float | None = Field(default=None, ge=0, le=1)
    ROOTS: float | None = Field(default=None, ge=0, le=1)


class MachineryWindows(DomainModel):
    """Meses calendario (1 a 12) con maquinaria disponible por operación."""

    SOWING: tuple[int, ...] | None = None
    HARVEST: tuple[int, ...] | None = None

    @model_validator(mode="after")
    def _months(self) -> MachineryWindows:
        for name in ("SOWING", "HARVEST"):
            months = getattr(self, name)
            if months is None:
                continue
            if any(m < 1 or m > 12 for m in months):
                raise ValueError(f"ventana de {name}: los meses deben estar entre 1 y 12")
            if len(set(months)) != len(months):
                raise ValueError(f"ventana de {name}: meses repetidos")
        return self


class ActorProfile(DomainModel):
    profile_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,31}$")
    label: str = Field(min_length=1)
    horizon_years: PValue
    soil_weight_alpha: PValue
    risk_aversion_lambda: PValue
    discount_rate: PValue
    constraints: Constraints
    priorities: SoilPriorities | None = None
    machinery_windows: MachineryWindows | None = None

    @model_validator(mode="after")
    def _ranges(self) -> ActorProfile:
        h = self.horizon_years
        if h.unit != "year" or not float(h.value).is_integer() or not (1 <= h.value <= 20):
            raise ValueError("el horizonte H debe ser un entero de 1 a 20 años")
        if self.soil_weight_alpha.unit != "USD/ha/point" or self.soil_weight_alpha.value < 0:
            raise ValueError("α debe estar en 'USD/ha/point' y ser mayor o igual a 0")
        if self.risk_aversion_lambda.unit != "ratio" or self.risk_aversion_lambda.value < 0:
            raise ValueError("λ debe ser un 'ratio' mayor o igual a 0")
        i = self.discount_rate
        if i.unit != "fraction" or not (0 <= i.value <= 1):
            raise ValueError("la tasa de descuento i debe ser una 'fraction' entre 0 y 1")
        return self

    @property
    def horizon(self) -> int:
        return int(self.horizon_years.value)
