"""ET0 FAO-56 Penman-Monteith.

Valores de referencia publicados en FAO Irrigation and Drainage Paper 56 (Allen et al.,
1998), cap. 3 y 4:

- Ejemplo 8: Ra el 3 de septiembre a 20°S = 32.2 MJ/m²/día.
- Ejemplo 18: Bruselas, 6 de julio, 50°48'N, 100 m s.n.m.; Tmax 21.5 °C, Tmin 12.3 °C,
  RHmax 84 %, RHmin 63 %, viento 10 km/h medido a 10 m, insolación real 9.25 h.
  Intermedios publicados: P 100.1 kPa, gamma 0.0666, Delta 0.122, es 1.997, ea 1.409,
  Ra 41.09, N 16.1 h, Rs 22.07, Rso 30.90, Rns 16.99, Rnl 3.71 MJ/m²/día, u2 2.078 m/s.
  Resultado publicado: ET0 = 3.9 mm/día.
"""

from __future__ import annotations

import math
from datetime import date

import pandas as pd
import pytest

from rastrojo.data import et0 as fao
from rastrojo.data.gaps import gap_report

LAT_BRUSSELS = 50 + 48 / 60
DOY_JULY_6 = 187
ELEV_BRUSSELS = 100.0


def test_example_8_extraterrestrial_radiation() -> None:
    doy = date(2015, 9, 3).timetuple().tm_yday  # 246 en año no bisiesto
    assert doy == 246
    assert fao.extraterrestrial_radiation_mj_m2_day(-20.0, doy) == pytest.approx(32.2, abs=0.05)


def test_example_18_intermediates() -> None:
    p = fao.atmospheric_pressure_kpa(ELEV_BRUSSELS)
    assert p == pytest.approx(100.1, abs=0.05)
    assert fao.psychrometric_constant_kpa_c(p) == pytest.approx(0.0666, abs=0.0001)
    assert fao.slope_vapour_pressure_curve_kpa_c(16.9) == pytest.approx(0.122, abs=0.0005)
    assert fao.mean_saturation_vapour_pressure_kpa(21.5, 12.3) == pytest.approx(1.997, abs=0.001)
    ea = fao.actual_vapour_pressure_from_rh_minmax_kpa(21.5, 12.3, 84, 63)
    assert ea == pytest.approx(1.409, abs=0.001)
    ra = fao.extraterrestrial_radiation_mj_m2_day(LAT_BRUSSELS, DOY_JULY_6)
    assert ra == pytest.approx(41.09, abs=0.01)
    assert fao.daylight_hours(LAT_BRUSSELS, DOY_JULY_6) == pytest.approx(16.1, abs=0.05)
    rs = fao.solar_radiation_from_sunshine_mj_m2_day(9.25, LAT_BRUSSELS, DOY_JULY_6)
    assert rs == pytest.approx(22.07, abs=0.01)
    rso = fao.clear_sky_radiation_mj_m2_day(ra, ELEV_BRUSSELS)
    assert rso == pytest.approx(30.90, abs=0.01)
    assert fao.net_shortwave_radiation_mj_m2_day(rs) == pytest.approx(16.99, abs=0.01)
    rnl = fao.net_longwave_radiation_mj_m2_day(21.5, 12.3, ea, rs, rso)
    assert rnl == pytest.approx(3.71, abs=0.01)
    assert fao.wind_speed_at_2m(10 / 3.6, 10.0) == pytest.approx(2.078, abs=0.001)


def test_example_18_et0() -> None:
    p = fao.atmospheric_pressure_kpa(ELEV_BRUSSELS)
    et0 = fao.penman_monteith_et0_mm_day(
        t_max_c=21.5,
        t_min_c=12.3,
        ea_kpa=fao.actual_vapour_pressure_from_rh_minmax_kpa(21.5, 12.3, 84, 63),
        rs_mj_m2_day=fao.solar_radiation_from_sunshine_mj_m2_day(9.25, LAT_BRUSSELS, DOY_JULY_6),
        u2_m_s=fao.wind_speed_at_2m(10 / 3.6, 10.0),
        pressure_kpa=p,
        latitude_deg=LAT_BRUSSELS,
        day_of_year=DOY_JULY_6,
        elevation_m=ELEV_BRUSSELS,
    )
    assert et0 == pytest.approx(3.9, abs=0.1)


def _power_day(**over: float) -> float:
    base: dict[str, float] = {
        "t_max_c": 30.0,
        "t_min_c": 16.0,
        "rh_mean_pct": 45.0,
        "ws2m_m_s": 2.5,
        "allsky_mj_m2_day": 24.0,
        "ps_kpa": 100.4,
        "latitude_deg": -33.07,
        "elevation_m": 76.0,
    }
    base.update(over)
    return fao.et0_from_power_day(day=date(2020, 1, 15), **base)


def test_et0_increases_with_radiation() -> None:
    values = [_power_day(allsky_mj_m2_day=rs) for rs in (8.0, 14.0, 20.0, 26.0, 32.0)]
    assert values == sorted(values)
    assert len(set(values)) == len(values)


def test_et0_increases_with_wind_in_dry_air() -> None:
    values = [_power_day(ws2m_m_s=u) for u in (0.5, 1.5, 3.0, 5.0)]
    assert values == sorted(values)


def test_et0_decreases_with_humidity() -> None:
    values = [_power_day(rh_mean_pct=rh) for rh in (30.0, 50.0, 70.0, 90.0)]
    assert values == sorted(values, reverse=True)


def test_rs_over_rso_is_capped_at_one() -> None:
    capped = fao.net_longwave_radiation_mj_m2_day(25, 15, 1.5, 40.0, 30.0)
    at_one = fao.net_longwave_radiation_mj_m2_day(25, 15, 1.5, 30.0, 30.0)
    assert capped == at_one


def _wide(rows: dict[str, list[float]]) -> pd.DataFrame:
    idx = pd.date_range("2020-01-01", periods=len(next(iter(rows.values()))), freq="D")
    return pd.DataFrame(rows, index=idx)


def test_et0_series_missing_input_gives_missing() -> None:
    wide = _wide(
        {
            "T2M_MAX": [30.0, 30.0, 30.0],
            "T2M_MIN": [16.0, 16.0, 16.0],
            "RH2M": [45.0, 45.0, 45.0],
            "WS2M": [2.5, 2.5, 2.5],
            "ALLSKY_SFC_SW_DWN": [24.0, math.nan, 24.0],
            "PS": [100.4, 100.4, 100.4],
        }
    )
    out = fao.et0_series(wide, latitude_deg=-33.07, elevation_m=76.0)
    assert out["is_missing"].tolist() == [False, True, False]
    assert out.loc[1, "missing_reason"] == "MISSING_INPUT"
    assert math.isnan(out.loc[1, "value"])
    report = gap_report(out, "DERIVED_ET0")
    assert report.missing_by_variable == {fao.ET0_VARIABLE: 1}
    assert report.entries[0].date == date(2020, 1, 2)


def test_et0_provenance_is_derived_with_inputs() -> None:
    prov = fao.ET0_PROVENANCE
    assert prov.kind == "DERIVED"
    assert prov.method == "FAO56_PENMAN_MONTEITH"
    for var in ("T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN", "PS"):
        assert f"NASA_POWER:{var}" in prov.derived_from
