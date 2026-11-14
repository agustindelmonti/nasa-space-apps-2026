"""Parámetros económicos: todos con procedencia y fecha, ninguno con valor por defecto."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from rastrojo.domain.base import DomainModel
from rastrojo.domain.climate import YearClass
from rastrojo.domain.crops import Crop
from rastrojo.domain.provenance import DatedPValue


class PriceBasis(StrEnum):
    FOB = "FOB"
    SPOT_FAS = "SPOT_FAS"


class HarvestCostMode(StrEnum):
    FRACTION_OF_REVENUE = "FRACTION_OF_REVENUE"
    USD_PER_HA = "USD_PER_HA"


def _require(
    name: str, pv: DatedPValue, unit: str, lo: float | None = None, hi: float | None = None
) -> None:
    if pv.unit != unit:
        raise ValueError(f"{name} debe estar en '{unit}' (recibido '{pv.unit}')")
    if lo is not None and pv.value < lo:
        raise ValueError(f"{name} debe ser mayor o igual a {lo:g}")
    if hi is not None and pv.value > hi:
        raise ValueError(f"{name} debe ser menor o igual a {hi:g}")


class CropEconomics(DomainModel):
    """Parámetros de un cultivo de renta. Los campos ausentes no tienen valor por defecto:
    economics los reporta como faltantes (error tipado) en lugar de inventarlos."""

    crop: Crop
    price: DatedPValue | None = None
    price_basis: PriceBasis | None = None
    export_tax: DatedPValue | None = None
    direct_costs: DatedPValue | None = None
    harvest_cost_mode: HarvestCostMode | None = None
    harvest_cost: DatedPValue | None = None
    marketing_cost: DatedPValue | None = None
    freight: DatedPValue | None = None
    yields: dict[YearClass, DatedPValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _units(self) -> CropEconomics:
        if self.price is not None:
            if self.price_basis is None:
                raise ValueError("price_basis: el precio debe declarar base FOB o SPOT_FAS")
            _require("precio", self.price, "USD/t", lo=0)
        if self.export_tax is not None:
            _require("retención", self.export_tax, "fraction", lo=0)
            if self.export_tax.value >= 1:
                raise ValueError("la retención debe ser menor a 1")
        if self.direct_costs is not None:
            _require("costos directos", self.direct_costs, "USD/ha", lo=0)
        if self.harvest_cost is not None:
            if self.harvest_cost_mode is None:
                raise ValueError("harvest_cost_mode: el costo de cosecha debe declarar su modo")
            if self.harvest_cost_mode is HarvestCostMode.FRACTION_OF_REVENUE:
                _require("costo de cosecha", self.harvest_cost, "fraction", lo=0, hi=1)
            else:
                _require("costo de cosecha", self.harvest_cost, "USD/ha", lo=0)
        if self.marketing_cost is not None:
            _require("comercialización", self.marketing_cost, "fraction", lo=0, hi=1)
        if self.freight is not None:
            _require("flete", self.freight, "USD/t", lo=0)
        for cls, pv in self.yields.items():
            _require(f"rinde {cls}", pv, "t/ha", lo=0, hi=25)
        return self

    def missing_parameters(self) -> tuple[str, ...]:
        names = [
            n
            for n in (
                "direct_costs",
                "export_tax",
                "freight",
                "harvest_cost",
                "marketing_cost",
                "price",
            )
            if getattr(self, n) is None
        ]
        names += [f"yield_{c.value.lower()}" for c in YearClass if c not in self.yields]
        return tuple(sorted(names))


class ServiceCropCosts(DomainModel):
    """Cultivo de servicio: solo costos (implantación, semilla, secado). Sin precio ni rinde."""

    crop: Crop
    direct_costs: DatedPValue

    @model_validator(mode="after")
    def _units(self) -> ServiceCropCosts:
        _require("costos directos del servicio", self.direct_costs, "USD/ha", lo=0)
        return self


class Rent(DomainModel):
    """Arrendamiento opcional, en una sola unidad."""

    usd_ha: DatedPValue | None = None
    soy_qq_ha: DatedPValue | None = None

    @model_validator(mode="after")
    def _one_unit(self) -> Rent:
        if (self.usd_ha is None) == (self.soy_qq_ha is None):
            raise ValueError(
                "el arrendamiento admite una sola unidad: USD/ha o quintales de soja/ha"
            )
        if self.usd_ha is not None:
            _require("arrendamiento", self.usd_ha, "USD/ha", lo=0)
        if self.soy_qq_ha is not None:
            _require("arrendamiento", self.soy_qq_ha, "qq/ha", lo=0)
        return self


class EconomicParameters(DomainModel):
    crops: tuple[CropEconomics, ...] = Field(min_length=1)
    service_crops: tuple[ServiceCropCosts, ...] = ()
    rent: Rent | None = None

    @model_validator(mode="after")
    def _unique(self) -> EconomicParameters:
        crops = [c.crop for c in self.crops] + [c.crop for c in self.service_crops]
        if len(set(crops)) != len(crops):
            raise ValueError("hay parámetros económicos repetidos para un mismo cultivo")
        return self

    def service_for(self, crop: Crop) -> ServiceCropCosts | None:
        for c in self.service_crops:
            if c.crop is crop:
                return c
        return None

    def for_crop(self, crop: Crop) -> CropEconomics | None:
        for c in self.crops:
            if c.crop is crop:
                return c
        return None
