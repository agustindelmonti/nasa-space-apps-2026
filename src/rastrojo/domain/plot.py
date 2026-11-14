"""Lote y suelo."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from rastrojo.domain.base import DomainModel
from rastrojo.domain.provenance import Provenance, PValue

# Bounding box aproximada de Argentina continental (decisión 8 del design).
AR_LAT_MIN, AR_LAT_MAX = -55.1, -21.7
AR_LON_MIN, AR_LON_MAX = -73.6, -53.6


class GeoPoint(DomainModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def _inside_argentina(self) -> GeoPoint:
        if not (AR_LAT_MIN <= self.lat <= AR_LAT_MAX and AR_LON_MIN <= self.lon <= AR_LON_MAX):
            raise ValueError(
                f"ubicación ({self.lat}, {self.lon}) fuera del área soportada (Argentina: "
                f"lat {AR_LAT_MIN} a {AR_LAT_MAX}, lon {AR_LON_MIN} a {AR_LON_MAX})"
            )
        return self


def _point_in_ring(lon: float, lat: float, ring: tuple[tuple[float, float], ...]) -> bool:
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > lat) != (y2 > lat):
            x_cross = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < x_cross:
                inside = not inside
    return inside


class PolygonGeometry(DomainModel):
    """Polígono GeoJSON simple (un anillo exterior, coordenadas [lon, lat])."""

    type: str = Field(pattern="^Polygon$")
    coordinates: tuple[tuple[tuple[float, float], ...], ...] = Field(min_length=1, max_length=1)

    @field_validator("coordinates")
    @classmethod
    def _ring_ok(
        cls, v: tuple[tuple[tuple[float, float], ...], ...]
    ) -> tuple[tuple[tuple[float, float], ...], ...]:
        ring = v[0]
        if len(ring) < 4:
            raise ValueError("el anillo del polígono necesita al menos 4 puntos (cerrado)")
        if ring[0] != ring[-1]:
            raise ValueError("el anillo del polígono debe cerrarse (primer punto = último)")
        return v

    def contains(self, point: GeoPoint) -> bool:
        return _point_in_ring(point.lon, point.lat, self.coordinates[0])


class Plot(DomainModel):
    plot_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,63}$")
    name: str = Field(min_length=1)
    location: GeoPoint
    area_ha: PValue
    polygon: PolygonGeometry | None = None

    @model_validator(mode="after")
    def _checks(self) -> Plot:
        if self.area_ha.unit != "ha" or self.area_ha.value <= 0:
            raise ValueError("la superficie del lote debe estar en 'ha' y ser mayor a 0")
        if self.polygon is not None and not self.polygon.contains(self.location):
            raise ValueError("la ubicación del lote no está dentro de su polígono")
        return self


class TextureClass(StrEnum):
    SAND = "SAND"
    LOAMY_SAND = "LOAMY_SAND"
    SANDY_LOAM = "SANDY_LOAM"
    LOAM = "LOAM"
    SILT_LOAM = "SILT_LOAM"
    SILT = "SILT"
    SANDY_CLAY_LOAM = "SANDY_CLAY_LOAM"
    CLAY_LOAM = "CLAY_LOAM"
    SILTY_CLAY_LOAM = "SILTY_CLAY_LOAM"
    SANDY_CLAY = "SANDY_CLAY"
    SILTY_CLAY = "SILTY_CLAY"
    CLAY = "CLAY"


class TextureValue(DomainModel):
    value: TextureClass
    provenance: Provenance


class FlagValue(DomainModel):
    value: bool
    provenance: Provenance


def _check_range(name: str, pv: PValue | None, unit: str, lo: float, hi: float) -> None:
    if pv is None:
        return
    if pv.unit != unit:
        raise ValueError(f"{name} debe estar en '{unit}' (recibido '{pv.unit}')")
    if not (lo <= pv.value <= hi):
        raise ValueError(f"{name} fuera de rango: {pv.value}; rango permitido {lo:g} a {hi:g}")


class Soil(DomainModel):
    """Suelo del lote. Cada campo es opcional y lleva su propia procedencia.

    Un campo ausente es un faltante explícito: nunca se completa con un valor por defecto.
    """

    texture: TextureValue | None = None
    organic_matter_pct: PValue | None = None
    available_water_mm: PValue | None = None
    root_depth_m: PValue | None = None
    water_table_depth_m: PValue | None = None
    compaction: FlagValue | None = None

    @model_validator(mode="after")
    def _ranges(self) -> Soil:
        _check_range("materia orgánica", self.organic_matter_pct, "%", 0, 100)
        _check_range("agua útil", self.available_water_mm, "mm", 0, 600)
        _check_range("profundidad de raíces", self.root_depth_m, "m", 0, 4)
        _check_range("profundidad de napa", self.water_table_depth_m, "m", 0, 30)
        return self

    def missing_fields(self) -> tuple[str, ...]:
        names = (
            "texture",
            "organic_matter_pct",
            "available_water_mm",
            "root_depth_m",
            "water_table_depth_m",
            "compaction",
        )
        return tuple(n for n in names if getattr(self, n) is None)
