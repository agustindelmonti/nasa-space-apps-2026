"""Evapotranspiración de referencia FAO-56 Penman-Monteith diaria (valor DERIVED).

Funciones puras, sin I/O. Referencia: Allen, R.G., Pereira, L.S., Raes, D., Smith, M.
(1998). *Crop evapotranspiration: Guidelines for computing crop water requirements*.
FAO Irrigation and Drainage Paper 56, cap. 3 y 4. Los números de ecuación de cada
función corresponden a ese documento.

Decisiones para insumos de NASA POWER (ver design de nasa-ingestion):

- Presión: se usa ``PS`` de POWER (kPa) en lugar de estimarla por altitud (ec. 7).
- Vapor real ``ea``: con humedad relativa media diaria ``RH2M`` (ec. 19), porque POWER
  no publica RHmax/RHmin en la comunidad AG.
- Temperatura media del día para Penman-Monteith: (Tmax + Tmin) / 2 (ec. 9), como pide
  FAO-56 para el cálculo diario.
- Radiación de cielo claro ``Rso``: ec. 37 con la radiación extraterrestre de la latitud
  y el día (ec. 21) y la elevación de la celda que informa POWER.
- Flujo de calor del suelo diario ``G = 0`` (ec. 42).
- Viento: ``WS2M`` ya está a 2 m; no hace falta la ec. 47.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from datetime import date

import pandas as pd

from rastrojo.data.schema import MissingReason
from rastrojo.domain import DerivedProvenance

SOLAR_CONSTANT_MJ_M2_MIN = 0.0820  # Gsc, ec. 21
STEFAN_BOLTZMANN_MJ_K4_M2_DAY = 4.903e-9  # sigma, ec. 39
ALBEDO_REFERENCE = 0.23  # pasto de referencia, ec. 38
ANGSTROM_AS = 0.25  # valores por defecto de FAO-56, ec. 35
ANGSTROM_BS = 0.50

ET0_VARIABLE = "ET0_FAO56"
ET0_UNIT = "mm/day"
ET0_METHOD = "FAO56_PENMAN_MONTEITH"
ET0_INPUTS: tuple[str, ...] = (
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "WS2M",
    "ALLSKY_SFC_SW_DWN",
    "PS",
)
ET0_PROVENANCE = DerivedProvenance(
    method=ET0_METHOD,
    derived_from=tuple(f"NASA_POWER:{v}" for v in ET0_INPUTS),
)


# --- Parámetros atmosféricos -------------------------------------------------------


def atmospheric_pressure_kpa(elevation_m: float) -> float:
    """Ec. 7: presión atmosférica estándar a una altitud dada."""
    return float(101.3 * ((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26)


def psychrometric_constant_kpa_c(pressure_kpa: float) -> float:
    """Ec. 8: constante psicrométrica (kPa/°C)."""
    return 0.000665 * pressure_kpa


def saturation_vapour_pressure_kpa(t_c: float) -> float:
    """Ec. 11: presión de vapor de saturación a la temperatura ``t_c``."""
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def mean_saturation_vapour_pressure_kpa(t_max_c: float, t_min_c: float) -> float:
    """Ec. 12."""
    return (saturation_vapour_pressure_kpa(t_max_c) + saturation_vapour_pressure_kpa(t_min_c)) / 2


def slope_vapour_pressure_curve_kpa_c(t_mean_c: float) -> float:
    """Ec. 13: pendiente de la curva de presión de vapor (Delta)."""
    return 4098.0 * saturation_vapour_pressure_kpa(t_mean_c) / (t_mean_c + 237.3) ** 2


def actual_vapour_pressure_from_rh_minmax_kpa(
    t_max_c: float, t_min_c: float, rh_max_pct: float, rh_min_pct: float
) -> float:
    """Ec. 17: ``ea`` desde humedad relativa máxima y mínima."""
    return (
        saturation_vapour_pressure_kpa(t_min_c) * rh_max_pct / 100.0
        + saturation_vapour_pressure_kpa(t_max_c) * rh_min_pct / 100.0
    ) / 2.0


def actual_vapour_pressure_from_rh_mean_kpa(
    t_max_c: float, t_min_c: float, rh_mean_pct: float
) -> float:
    """Ec. 19: ``ea`` desde humedad relativa media diaria."""
    return rh_mean_pct / 100.0 * mean_saturation_vapour_pressure_kpa(t_max_c, t_min_c)


def wind_speed_at_2m(u_z_m_s: float, height_m: float) -> float:
    """Ec. 47: lleva el viento medido a ``height_m`` a 2 m sobre el suelo."""
    return u_z_m_s * 4.87 / math.log(67.8 * height_m - 5.42)


# --- Radiación ----------------------------------------------------------------------


def _solar_geometry(latitude_deg: float, day_of_year: int) -> tuple[float, float, float, float]:
    phi = math.radians(latitude_deg)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)  # ec. 23
    delta = 0.409 * math.sin(2.0 * math.pi * day_of_year / 365.0 - 1.39)  # ec. 24
    arg = -math.tan(phi) * math.tan(delta)
    omega_s = math.acos(max(-1.0, min(1.0, arg)))  # ec. 25
    return phi, dr, delta, omega_s


def extraterrestrial_radiation_mj_m2_day(latitude_deg: float, day_of_year: int) -> float:
    """Ec. 21: radiación extraterrestre diaria Ra (MJ/m²/día)."""
    phi, dr, delta, omega_s = _solar_geometry(latitude_deg, day_of_year)
    return (
        24.0
        * 60.0
        / math.pi
        * SOLAR_CONSTANT_MJ_M2_MIN
        * dr
        * (
            omega_s * math.sin(phi) * math.sin(delta)
            + math.cos(phi) * math.cos(delta) * math.sin(omega_s)
        )
    )


def daylight_hours(latitude_deg: float, day_of_year: int) -> float:
    """Ec. 34: duración máxima posible de insolación N (horas)."""
    _, _, _, omega_s = _solar_geometry(latitude_deg, day_of_year)
    return 24.0 / math.pi * omega_s


def solar_radiation_from_sunshine_mj_m2_day(
    sunshine_hours: float, latitude_deg: float, day_of_year: int
) -> float:
    """Ec. 35 (Angström) con a_s = 0.25 y b_s = 0.50."""
    ra = extraterrestrial_radiation_mj_m2_day(latitude_deg, day_of_year)
    n_max = daylight_hours(latitude_deg, day_of_year)
    return (ANGSTROM_AS + ANGSTROM_BS * sunshine_hours / n_max) * ra


def clear_sky_radiation_mj_m2_day(ra_mj_m2_day: float, elevation_m: float) -> float:
    """Ec. 37: radiación de cielo claro Rso."""
    return (0.75 + 2e-5 * elevation_m) * ra_mj_m2_day


def net_shortwave_radiation_mj_m2_day(rs_mj_m2_day: float) -> float:
    """Ec. 38 con albedo 0.23."""
    return (1.0 - ALBEDO_REFERENCE) * rs_mj_m2_day


def net_longwave_radiation_mj_m2_day(
    t_max_c: float, t_min_c: float, ea_kpa: float, rs_mj_m2_day: float, rso_mj_m2_day: float
) -> float:
    """Ec. 39: radiación neta de onda larga Rnl. Rs/Rso se limita a 1.0."""
    if rso_mj_m2_day <= 0:
        raise ValueError("Rso debe ser positiva para calcular Rnl")
    ratio = min(rs_mj_m2_day / rso_mj_m2_day, 1.0)
    t_max_k4 = (t_max_c + 273.16) ** 4
    t_min_k4 = (t_min_c + 273.16) ** 4
    return (
        STEFAN_BOLTZMANN_MJ_K4_M2_DAY
        * (t_max_k4 + t_min_k4)
        / 2.0
        * (0.34 - 0.14 * math.sqrt(ea_kpa))
        * (1.35 * ratio - 0.35)
    )


# --- Penman-Monteith ----------------------------------------------------------------


def penman_monteith_et0_mm_day(
    *,
    t_max_c: float,
    t_min_c: float,
    ea_kpa: float,
    rs_mj_m2_day: float,
    u2_m_s: float,
    pressure_kpa: float,
    latitude_deg: float,
    day_of_year: int,
    elevation_m: float,
    soil_heat_flux_mj_m2_day: float = 0.0,
) -> float:
    """Ec. 6: ET0 de referencia diaria (mm/día) con todos los insumos explícitos."""
    t_mean = (t_max_c + t_min_c) / 2.0
    delta = slope_vapour_pressure_curve_kpa_c(t_mean)
    gamma = psychrometric_constant_kpa_c(pressure_kpa)
    es = mean_saturation_vapour_pressure_kpa(t_max_c, t_min_c)
    ra = extraterrestrial_radiation_mj_m2_day(latitude_deg, day_of_year)
    rso = clear_sky_radiation_mj_m2_day(ra, elevation_m)
    rns = net_shortwave_radiation_mj_m2_day(rs_mj_m2_day)
    rnl = net_longwave_radiation_mj_m2_day(t_max_c, t_min_c, ea_kpa, rs_mj_m2_day, rso)
    rn = rns - rnl
    numerator = 0.408 * delta * (rn - soil_heat_flux_mj_m2_day) + gamma * (
        900.0 / (t_mean + 273.0)
    ) * u2_m_s * (es - ea_kpa)
    denominator = delta + gamma * (1.0 + 0.34 * u2_m_s)
    return numerator / denominator


def et0_from_power_day(
    *,
    day: date,
    t_max_c: float,
    t_min_c: float,
    rh_mean_pct: float,
    ws2m_m_s: float,
    allsky_mj_m2_day: float,
    ps_kpa: float,
    latitude_deg: float,
    elevation_m: float,
) -> float:
    """ET0 de un día con las variables de POWER (ver decisiones del módulo)."""
    ea = actual_vapour_pressure_from_rh_mean_kpa(t_max_c, t_min_c, rh_mean_pct)
    return penman_monteith_et0_mm_day(
        t_max_c=t_max_c,
        t_min_c=t_min_c,
        ea_kpa=ea,
        rs_mj_m2_day=allsky_mj_m2_day,
        u2_m_s=ws2m_m_s,
        pressure_kpa=ps_kpa,
        latitude_deg=latitude_deg,
        day_of_year=day.timetuple().tm_yday,
        elevation_m=elevation_m,
    )


def et0_series(
    wide: pd.DataFrame,
    *,
    latitude_deg: float,
    elevation_m: float,
    inputs: Sequence[str] = ET0_INPUTS,
) -> pd.DataFrame:
    """ET0 diaria en formato largo desde un frame ancho de POWER (una fila por día).

    Un día con cualquier insumo faltante da ET0 faltante con motivo ``MISSING_INPUT``:
    no se interpola ni se completa con otro día.
    """
    missing_cols = [c for c in inputs if c not in wide.columns]
    if missing_cols:
        raise ValueError(f"faltan columnas para ET0: {', '.join(missing_cols)}")
    rows: list[dict[str, object]] = []
    for ts, row in wide.sort_index().iterrows():
        day = pd.Timestamp(ts).date()  # type: ignore[arg-type]
        if any(pd.isna(row[c]) for c in inputs):
            rows.append(
                {
                    "date": pd.Timestamp(day),
                    "variable": ET0_VARIABLE,
                    "value": math.nan,
                    "unit": ET0_UNIT,
                    "is_missing": True,
                    "missing_reason": MissingReason.MISSING_INPUT.value,
                }
            )
            continue
        value = et0_from_power_day(
            day=day,
            t_max_c=float(row["T2M_MAX"]),
            t_min_c=float(row["T2M_MIN"]),
            rh_mean_pct=float(row["RH2M"]),
            ws2m_m_s=float(row["WS2M"]),
            allsky_mj_m2_day=float(row["ALLSKY_SFC_SW_DWN"]),
            ps_kpa=float(row["PS"]),
            latitude_deg=latitude_deg,
            elevation_m=elevation_m,
        )
        rows.append(
            {
                "date": pd.Timestamp(day),
                "variable": ET0_VARIABLE,
                "value": value,
                "unit": ET0_UNIT,
                "is_missing": False,
                "missing_reason": None,
            }
        )
    df = pd.DataFrame(
        rows, columns=["date", "variable", "value", "unit", "is_missing", "missing_reason"]
    )
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    df["value"] = df["value"].astype("float64")
    df["is_missing"] = df["is_missing"].astype(bool)
    df["variable"] = df["variable"].astype(object)
    df["unit"] = df["unit"].astype(object)
    df["missing_reason"] = df["missing_reason"].astype(object)
    return df
