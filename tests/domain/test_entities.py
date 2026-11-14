from __future__ import annotations

import pytest
from pydantic import ValidationError

from rastrojo.domain import (
    CROP_INFO,
    Campaign,
    ClimateScenario,
    Constraints,
    Crop,
    GeoPoint,
    MachineryWindows,
    PolygonGeometry,
    Rent,
    Rotation,
    ScenarioSet,
    Soil,
    SoilPriorities,
    YearClass,
)
from tests.domain.factories import crop_economics, dated, plot, profile, pv, scenario


# Lote
def test_location_outside_argentina() -> None:
    with pytest.raises(ValidationError, match="fuera del área soportada"):
        GeoPoint(lat=40.7, lon=-74.0)


def test_valid_core_zone_plot() -> None:
    p = plot()
    assert p.area_ha.value == 100


def test_point_must_be_inside_polygon() -> None:
    poly = PolygonGeometry(
        type="Polygon",
        coordinates=(
            (
                (-61.13, -33.08),
                (-61.11, -33.08),
                (-61.11, -33.06),
                (-61.13, -33.06),
                (-61.13, -33.08),
            ),
        ),
    )
    assert plot(polygon=poly).polygon is not None
    with pytest.raises(ValidationError, match="polígono"):
        plot(polygon=poly, location=GeoPoint(lat=-33.2, lon=-61.3))


def test_plot_is_frozen() -> None:
    p = plot()
    with pytest.raises(ValidationError):
        p.name = "otro"  # type: ignore[misc]


# Suelo
def test_organic_matter_out_of_range() -> None:
    with pytest.raises(ValidationError, match="rango permitido 0 a 100"):
        Soil(organic_matter_pct=pv(150, "%"))


def test_partial_soil_reports_missing() -> None:
    s = Soil(organic_matter_pct=pv(2.8, "%"))
    assert s.available_water_mm is None
    assert "available_water_mm" in s.missing_fields()
    assert "organic_matter_pct" not in s.missing_fields()


# Cultivos y rotación
def test_calendar_from_single_assumption() -> None:
    assert {info.calendar_assumption_id for info in CROP_INFO.values()} == {"A-AGR-01"}


def test_crop_out_of_catalog() -> None:
    with pytest.raises(ValidationError, match="SOY_1ST"):
        Campaign(summer="girasol")  # type: ignore[arg-type]


def test_soy_second_without_predecessor() -> None:
    with pytest.raises(ValidationError, match="antecesor"):
        Campaign(summer=Crop.SOY_2ND)


def test_wheat_soy2_maize_valid() -> None:
    r = Rotation(
        rotation_id="R_WHEAT_SOY2_MAIZE",
        name="Trigo/Soja 2da → Maíz",
        campaigns=(
            Campaign(winter=Crop.WHEAT, summer=Crop.SOY_2ND),
            Campaign(summer=Crop.MAIZE_EARLY),
        ),
    )
    assert r.cycle_length == 2
    assert r.campaigns[0].is_double_crop


def test_rotation_is_frozen() -> None:
    r = Rotation(rotation_id="R_SOY_MONO", name="Soja", campaigns=(Campaign(summer=Crop.SOY_1ST),))
    with pytest.raises(ValidationError):
        r.name = "otra"  # type: ignore[misc]
    assert r.name == "Soja"


# Perfil
def test_invalid_horizon() -> None:
    with pytest.raises(ValidationError, match="H"):
        profile(horizon_years=pv(0, "year"))


def test_no_capital_cap() -> None:
    c = Constraints(allow_double_crop=True, allow_cover_crop=False)
    assert c.max_working_capital_usd_ha is None


def test_priority_out_of_range() -> None:
    with pytest.raises(ValidationError):
        SoilPriorities(NITROGEN=1.5)


def test_water_priority_not_declared() -> None:
    with pytest.raises(ValidationError, match="WATER"):
        SoilPriorities.model_validate({"WATER": 0.5})


def test_invalid_machinery_month() -> None:
    with pytest.raises(ValidationError, match="1 y 12"):
        MachineryWindows(SOWING=(11, 13))


# Economía
def test_price_without_date() -> None:
    with pytest.raises(ValidationError, match="reference_date"):
        crop_economics(price={"value": 300, "unit": "USD/t", "provenance": {"kind": "USER_INPUT"}})


def test_price_without_basis() -> None:
    data = crop_economics(Crop.MAIZE_EARLY).model_dump()
    del data["price_basis"]
    with pytest.raises(ValidationError, match="price_basis"):
        type(crop_economics()).model_validate(data)


def test_rent_two_units() -> None:
    with pytest.raises(ValidationError, match="una sola unidad"):
        Rent(usd_ha=dated(250, "USD/ha"), soy_qq_ha=dated(12, "qq/ha"))


# Clima
def test_seasonal_and_annual_classes() -> None:
    s = ClimateScenario(
        campaign_start_year=2008,
        annual_class=YearClass.NORMAL,
        winter_class=YearClass.DRY,
        summer_class=YearClass.WET,
        winter_rain=pv(180, "mm"),
        summer_rain=pv(700, "mm"),
        weight=1.0,
    )
    assert (s.annual_class, s.winter_class, s.summer_class) == (
        YearClass.NORMAL,
        YearClass.DRY,
        YearClass.WET,
    )


def test_weights_must_sum_one() -> None:
    with pytest.raises(ValidationError, match="sumar 1"):
        ScenarioSet(scenarios=(scenario(2008, 0.5), scenario(2009, 0.4)))
