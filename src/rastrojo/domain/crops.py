"""Catálogo cerrado de cultivos y rotaciones."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from rastrojo.domain.base import DomainModel


class Crop(StrEnum):
    SOY_1ST = "SOY_1ST"
    SOY_2ND = "SOY_2ND"
    MAIZE_EARLY = "MAIZE_EARLY"
    MAIZE_LATE = "MAIZE_LATE"
    WHEAT = "WHEAT"
    COVER_VETCH = "COVER_VETCH"
    COVER_RYE = "COVER_RYE"
    COVER_OAT = "COVER_OAT"


class Season(StrEnum):
    WINTER = "WINTER"
    SUMMER = "SUMMER"


class CropKind(StrEnum):
    CASH = "CASH"
    SERVICE = "SERVICE"


class Family(StrEnum):
    LEGUME = "LEGUME"
    GRASS = "GRASS"


CROP_CALENDAR_ASSUMPTION = "A-AGR-01"
"""Único supuesto de calendario (siembra y cosecha) compartido por todo el sistema."""


@dataclass(frozen=True, slots=True)
class CropInfo:
    label_es: str
    season: Season
    kind: CropKind
    family: Family
    calendar_assumption_id: str = CROP_CALENDAR_ASSUMPTION


CROP_INFO: dict[Crop, CropInfo] = {
    Crop.SOY_1ST: CropInfo("Soja de primera", Season.SUMMER, CropKind.CASH, Family.LEGUME),
    Crop.SOY_2ND: CropInfo("Soja de segunda", Season.SUMMER, CropKind.CASH, Family.LEGUME),
    Crop.MAIZE_EARLY: CropInfo("Maíz temprano", Season.SUMMER, CropKind.CASH, Family.GRASS),
    Crop.MAIZE_LATE: CropInfo("Maíz tardío", Season.SUMMER, CropKind.CASH, Family.GRASS),
    Crop.WHEAT: CropInfo("Trigo", Season.WINTER, CropKind.CASH, Family.GRASS),
    Crop.COVER_VETCH: CropInfo("Vicia (servicio)", Season.WINTER, CropKind.SERVICE, Family.LEGUME),
    Crop.COVER_RYE: CropInfo("Centeno (servicio)", Season.WINTER, CropKind.SERVICE, Family.GRASS),
    Crop.COVER_OAT: CropInfo("Avena (servicio)", Season.WINTER, CropKind.SERVICE, Family.GRASS),
}

DOUBLE_CROP_SUMMER: frozenset[Crop] = frozenset({Crop.SOY_2ND, Crop.MAIZE_LATE})


def _crop_from_any(value: object) -> object:
    if isinstance(value, str) and value not in Crop.__members__:
        allowed = ", ".join(c.value for c in Crop)
        raise ValueError(f"cultivo '{value}' fuera del catálogo; permitidos: {allowed}")
    return value


class Campaign(DomainModel):
    """Una campaña agrícola: a lo sumo un cultivo de invierno y uno de verano."""

    winter: Crop | None = None
    summer: Crop | None = None

    @field_validator("winter", "summer", mode="before")
    @classmethod
    def _in_catalog(cls, v: object) -> object:
        return _crop_from_any(v)

    @model_validator(mode="after")
    def _rules(self) -> Campaign:
        if self.winter is None and self.summer is None:
            raise ValueError("la campaña necesita al menos un cultivo")
        if self.winter is not None and CROP_INFO[self.winter].season is not Season.WINTER:
            raise ValueError(f"{self.winter} no es un cultivo de invierno")
        if self.summer is not None and CROP_INFO[self.summer].season is not Season.SUMMER:
            raise ValueError(f"{self.summer} no es un cultivo de verano")
        if self.summer in DOUBLE_CROP_SUMMER and self.winter is None:
            raise ValueError(
                f"{self.summer} necesita un cultivo de invierno antecesor en la misma campaña"
            )
        return self

    @property
    def is_double_crop(self) -> bool:
        return (
            self.winter is not None
            and CROP_INFO[self.winter].kind is CropKind.CASH
            and self.summer is not None
        )

    @property
    def has_cover_crop(self) -> bool:
        return self.winter is not None and CROP_INFO[self.winter].kind is CropKind.SERVICE


class Rotation(DomainModel):
    rotation_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]{1,63}$")
    name: str = Field(min_length=1)
    campaigns: tuple[Campaign, ...] = Field(min_length=1, max_length=4)

    @property
    def cycle_length(self) -> int:
        return len(self.campaigns)
