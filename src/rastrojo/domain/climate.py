"""Escenarios climáticos históricos e insumos hídricos del motor."""

from __future__ import annotations

import math
from datetime import date
from enum import StrEnum

from pydantic import Field, model_validator

from rastrojo.domain.base import DomainModel
from rastrojo.domain.provenance import Provenance, PValue, Source


class YearClass(StrEnum):
    DRY = "DRY"
    NORMAL = "NORMAL"
    WET = "WET"


class YearClassFilter(StrEnum):
    ALL = "ALL"
    DRY = "DRY"
    NORMAL = "NORMAL"
    WET = "WET"


class ClimateScenario(DomainModel):
    """Un año histórico real, identificado por el año de inicio de campaña."""

    campaign_start_year: int = Field(ge=1981, le=2100)
    annual_class: YearClass
    winter_class: YearClass
    summer_class: YearClass
    winter_rain: PValue
    summer_rain: PValue
    weight: float = Field(ge=0)

    @model_validator(mode="after")
    def _units(self) -> ClimateScenario:
        for name in ("winter_rain", "summer_rain"):
            pv: PValue = getattr(self, name)
            if pv.unit != "mm" or pv.value < 0:
                raise ValueError(f"{name} debe estar en 'mm' y ser mayor o igual a 0")
        return self


WEIGHT_TOLERANCE = 1e-9


def check_weights(scenarios: tuple[ClimateScenario, ...]) -> None:
    total = math.fsum(s.weight for s in scenarios)
    if abs(total - 1.0) > WEIGHT_TOLERANCE:
        raise ValueError(f"los pesos de los escenarios deben sumar 1 (suman {total:.12g})")


class ScenarioSet(DomainModel):
    scenarios: tuple[ClimateScenario, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _weights(self) -> ScenarioSet:
        check_weights(self.scenarios)
        years = [s.campaign_start_year for s in self.scenarios]
        if len(set(years)) != len(years):
            raise ValueError("hay años de campaña repetidos")
        return self


class WeatherSources(DomainModel):
    rain: Source
    et0: Provenance
    t2m_min: Source
    t2m_max: Source
    imerg_rain: Source | None = None


class ScenarioWeather(DomainModel):
    """Series diarias completas de un año de campaña (sin huecos: los años
    incompletos se excluyen antes en climate-scenarios)."""

    campaign_start_year: int = Field(ge=1981, le=2100)
    start_date: date
    rain_mm: tuple[float, ...] = Field(min_length=1)
    et0_mm: tuple[float, ...] = Field(min_length=1)
    t2m_min_c: tuple[float, ...] = Field(min_length=1)
    t2m_max_c: tuple[float, ...] = Field(min_length=1)
    imerg_rain_mm: tuple[float, ...] | None = None
    sources: WeatherSources

    @model_validator(mode="after")
    def _series(self) -> ScenarioWeather:
        n = len(self.rain_mm)
        series = {
            "et0_mm": self.et0_mm,
            "t2m_min_c": self.t2m_min_c,
            "t2m_max_c": self.t2m_max_c,
        }
        if self.imerg_rain_mm is not None:
            series["imerg_rain_mm"] = self.imerg_rain_mm
            if self.sources.imerg_rain is None:
                raise ValueError("hay serie IMERG pero falta su Source")
        for name, s in series.items():
            if len(s) != n:
                raise ValueError(f"{name} tiene {len(s)} días y rain_mm tiene {n}")
        if any(v < 0 for v in self.rain_mm) or any(v < 0 for v in self.et0_mm):
            raise ValueError("lluvia y ET0 no pueden ser negativas")
        if self.imerg_rain_mm is not None and any(v < 0 for v in self.imerg_rain_mm):
            raise ValueError("la lluvia IMERG no puede ser negativa")
        temps = self.t2m_min_c + self.t2m_max_c
        if any(t < -40 or t > 60 for t in temps):
            raise ValueError("temperaturas fuera de rango físico (-40 a 60 °C)")
        if any(lo > hi for lo, hi in zip(self.t2m_min_c, self.t2m_max_c, strict=True)):
            raise ValueError("T2M_MIN mayor que T2M_MAX en algún día")
        return self


class WaterInputs(DomainModel):
    """Insumos hídricos y de evidencia. El motor calcula la factibilidad desde acá."""

    weather: tuple[ScenarioWeather, ...] = Field(min_length=1)
    smap_initial_rootzone: PValue | None = None
    grace_tws_anomaly: PValue | None = None
    ndvi_monthly: tuple[PValue, ...] | None = None

    @model_validator(mode="after")
    def _checks(self) -> WaterInputs:
        years = [w.campaign_start_year for w in self.weather]
        if len(set(years)) != len(years):
            raise ValueError("hay años repetidos en las series diarias")
        smap = self.smap_initial_rootzone
        if smap is not None and (smap.unit != "m3/m3" or not (0 <= smap.value <= 0.7)):
            raise ValueError("la humedad SMAP debe estar en 'm3/m3' entre 0 y 0.7")
        tws = self.grace_tws_anomaly
        if tws is not None and tws.unit != "mm":
            raise ValueError("la anomalía TWS de GRACE-FO debe estar en 'mm'")
        if self.ndvi_monthly is not None:
            if len(self.ndvi_monthly) != 12:
                raise ValueError("el resumen NDVI mensual debe tener 12 valores")
            if any(v.unit != "index" or not (-1 <= v.value <= 1) for v in self.ndvi_monthly):
                raise ValueError("NDVI debe ser un 'index' entre -1 y 1")
        return self
