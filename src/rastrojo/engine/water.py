"""Factibilidad hídrica (agua disponible): balance diario tipo balde FAO-56 por escenario.

Submódulo puro del motor. Recibe todo resuelto desde `EngineInput` (series diarias por año,
Suelo, humedad SMAP, anomalía GRACE-FO y supuestos). Sin red, reloj, archivos ni azar; las
sumas se hacen en orden cronológico con `math.fsum`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field, JsonValue

from rastrojo.domain.base import DomainModel
from rastrojo.domain.climate import ClimateScenario, ScenarioWeather, WaterInputs, YearClass
from rastrojo.domain.crops import CROP_INFO, Campaign, Crop, CropKind, Rotation
from rastrojo.domain.engine_io import ResolvedAssumption
from rastrojo.domain.plot import Soil
from rastrojo.domain.provenance import (
    AssumptionProvenance,
    Dataset,
    DerivedProvenance,
    ObservedProvenance,
    Period,
    PValue,
)
from rastrojo.domain.results import (
    Evidence,
    MissingInfo,
    Risk,
    RiskType,
    Severity,
    VulnerabilityEntry,
    WaterFeasibility,
)

WATER_ASSUMPTIONS: tuple[str, ...] = (
    "A-AGR-01",
    "A-CLI-01",
    "A-CLI-03",
    "A-CLI-05",
    "A-CLI-06",
    "A-CLI-07",
    "A-CLI-08",
    "A-CLI-09",
    "A-CLI-10",
    "A-WAT-01",
    "A-WAT-02",
    "A-WAT-03",
    "A-WAT-04",
    "A-WAT-05",
    "A-WAT-06",
    "A-WAT-07",
    "A-WAT-08",
    "A-WAT-09",
    "A-WAT-10",
    "A-WAT-11",
    "A-WAT-12",
    "A-WAT-13",
    "A-WAT-14",
    "A-WAT-15",
    "A-WAT-16",
)

_STATE_ORDER = {
    WaterFeasibility.FEASIBLE: 0,
    WaterFeasibility.RISKY: 1,
    WaterFeasibility.UNKNOWN: 2,
    WaterFeasibility.NOT_FEASIBLE: 3,
}


def worst(states: list[WaterFeasibility]) -> WaterFeasibility:
    """Peor estado con el orden NOT_FEASIBLE > UNKNOWN > RISKY > FEASIBLE."""
    return max(states, key=lambda s: _STATE_ORDER[s]) if states else WaterFeasibility.UNKNOWN


class WaterAssumptionError(ValueError):
    """Falta un supuesto necesario en `resolved_assumptions` o tiene forma inválida."""


# ---------------------------------------------------------------------------
# Configuración resuelta desde los supuestos
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CropDates:
    sow: tuple[int, int, int]  # (offset de año, mes, día)
    harvest: tuple[int, int, int]


@dataclass(frozen=True)
class WaterConfig:
    calendar: dict[Crop, CropDates]
    winter_start: tuple[int, int]
    kc: dict[Crop, tuple[float, float, float]]
    stage_fractions: tuple[float, float, float, float]
    fallow_kc: float
    p: dict[str, float]
    rain_fraction: float
    moderate: float
    severe: float
    feasible_max_freq: float
    not_feasible_freq: float
    min_recharge_fraction: float
    cover_termination_days: int
    grace_threshold_mm: float
    water_table_range: tuple[float, float]
    fallback_initial_fraction: float
    theta: dict[str, tuple[float, float]]
    awc_reference_depth_m: float
    awc_generic_mm: float
    min_scenarios: int
    frost_threshold: float
    frost_windows: dict[Crop, tuple[int, int]]
    level_medium: float
    level_high: float
    heat_threshold: float
    flowering_windows: dict[Crop, tuple[int, int]]
    extreme_percentile: float


def _get(resolved: dict[str, ResolvedAssumption], aid: str) -> Any:
    if aid not in resolved:
        raise WaterAssumptionError(f"falta el supuesto {aid} en resolved_assumptions")
    return resolved[aid].value


def _md(text: str) -> tuple[int, int, int]:
    raw = str(text)
    offset = 0
    if raw.startswith("+1-"):
        offset, raw = 1, raw[3:]
    m, d = (int(x) for x in raw.split("-"))
    return offset, m, d


def _windows(value: Any) -> dict[Crop, tuple[int, int]]:
    return {Crop(k): (int(v[0]), int(v[1])) for k, v in dict(value).items()}


def water_config(resolved: dict[str, ResolvedAssumption]) -> WaterConfig:
    try:
        cal = {
            Crop(k): CropDates(_md(v["sow"]), _md(v["harvest"]))
            for k, v in dict(_get(resolved, "A-AGR-01")).items()
        }
        winter = dict(_get(resolved, "A-CLI-01"))["winter"]
        ws = _md(winter["start"])
        kc_raw = dict(_get(resolved, "A-WAT-01"))
        theta_raw = dict(_get(resolved, "A-WAT-13"))
        awc = dict(_get(resolved, "A-WAT-14"))
        levels = dict(_get(resolved, "A-CLI-07"))
        wt = _get(resolved, "A-WAT-11")
        sf = tuple(float(x) for x in kc_raw["stage_fractions"])
        return WaterConfig(
            calendar=cal,
            winter_start=(ws[1], ws[2]),
            kc={
                Crop(k): (float(v[0]), float(v[1]), float(v[2])) for k, v in kc_raw["crops"].items()
            },
            stage_fractions=(sf[0], sf[1], sf[2], sf[3]),
            fallow_kc=float(kc_raw["fallow_kc"]),
            p={str(k): float(v) for k, v in dict(_get(resolved, "A-WAT-03")).items()},
            rain_fraction=float(_get(resolved, "A-WAT-02")),
            moderate=float(_get(resolved, "A-WAT-04")),
            severe=float(_get(resolved, "A-WAT-05")),
            feasible_max_freq=float(_get(resolved, "A-WAT-06")),
            not_feasible_freq=float(_get(resolved, "A-WAT-07")),
            min_recharge_fraction=float(_get(resolved, "A-WAT-08")),
            cover_termination_days=int(_get(resolved, "A-WAT-09")),
            grace_threshold_mm=float(_get(resolved, "A-WAT-10")),
            water_table_range=(float(wt[0]), float(wt[1])),
            fallback_initial_fraction=float(_get(resolved, "A-WAT-12")),
            theta={str(k): (float(v[0]), float(v[1])) for k, v in theta_raw.items()},
            awc_reference_depth_m=float(awc["reference_root_depth_m"]),
            awc_generic_mm=float(awc["generic_mm"]),
            min_scenarios=int(_get(resolved, "A-CLI-03")),
            frost_threshold=float(_get(resolved, "A-CLI-05")),
            frost_windows=_windows(_get(resolved, "A-CLI-06")),
            level_medium=float(levels["medium"]),
            level_high=float(levels["high"]),
            heat_threshold=float(_get(resolved, "A-CLI-08")),
            flowering_windows=_windows(_get(resolved, "A-CLI-09")),
            extreme_percentile=float(_get(resolved, "A-CLI-10")),
        )
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        if isinstance(exc, WaterAssumptionError):
            raise
        raise WaterAssumptionError(f"supuesto hídrico con forma inválida: {exc}") from exc


# ---------------------------------------------------------------------------
# Modelos de salida
# ---------------------------------------------------------------------------


class ReasonCode(StrEnum):
    SEVERE_STRESS_FREQUENT = "SEVERE_STRESS_FREQUENT"
    MODERATE_STRESS = "MODERATE_STRESS"
    PROFILE_NOT_RECHARGED_AT_SOWING = "PROFILE_NOT_RECHARGED_AT_SOWING"
    GRACE_REGIONAL_DEFICIT = "GRACE_REGIONAL_DEFICIT"
    SHALLOW_WATER_TABLE_MITIGATES = "SHALLOW_WATER_TABLE_MITIGATES"
    INITIAL_MOISTURE_ASSUMED = "INITIAL_MOISTURE_ASSUMED"
    SOIL_AWC_ASSUMED = "SOIL_AWC_ASSUMED"
    SOIL_AWC_FROM_SOILGRIDS = "SOIL_AWC_FROM_SOILGRIDS"
    SCENARIOS_EXCLUDED = "SCENARIOS_EXCLUDED"
    INSUFFICIENT_SCENARIOS = "INSUFFICIENT_SCENARIOS"
    MISSING_WEATHER = "MISSING_WEATHER"
    CONSERVATIVE_RAIN_SOURCE = "CONSERVATIVE_RAIN_SOURCE"
    DETERMINED_BY_CAMPAIGN = "DETERMINED_BY_CAMPAIGN"


class Reason(DomainModel):
    code: ReasonCode
    params: dict[str, JsonValue] = Field(default_factory=dict)
    assumption_ids: tuple[str, ...] = ()


StressLabel = Literal["NONE", "MODERATE", "SEVERE"]


class CropScenarioWater(DomainModel):
    crop: Crop
    stress_index: PValue
    deficit: PValue
    label: StressLabel
    status: WaterFeasibility


class ScenarioWater(DomainModel):
    campaign_start_year: int
    annual_class: YearClass
    excluded: bool
    rain_source: Dataset | None = None
    crops: tuple[CropScenarioWater, ...] = ()
    water_at_summer_sowing: PValue | None = None
    fraction_at_summer_sowing: float | None = None
    fallow_water_at_summer_sowing: PValue | None = None


class ClassRange(DomainModel):
    year_class: YearClass
    count: int
    deficit_min: PValue | None = None
    deficit_mean: PValue | None = None
    deficit_max: PValue | None = None
    sowing_water_min: PValue | None = None
    sowing_water_mean: PValue | None = None
    sowing_water_max: PValue | None = None
    empty_reason: str | None = None


class CropScenarioStatus(DomainModel):
    """Estado por (cultivo, posición, escenario) que consume rotation-engine."""

    crop: Crop
    campaign_index: int
    campaign_start_year: int
    status: WaterFeasibility


class CampaignWater(DomainModel):
    campaign_index: int
    status: WaterFeasibility
    reasons: tuple[Reason, ...]
    valid_scenarios: int
    severe_frequency: PValue | None
    scenarios: tuple[ScenarioWater, ...]
    ranges: tuple[ClassRange, ...]
    cover_water_cost: PValue | None = None


class WaterAssessment(DomainModel):
    rotation_id: str
    status: WaterFeasibility
    reasons: tuple[Reason, ...]
    awc: PValue
    initial_water: PValue
    campaigns: tuple[CampaignWater, ...]
    crop_status: tuple[CropScenarioStatus, ...]
    vulnerability: tuple[VulnerabilityEntry, ...]
    evidence: tuple[Evidence, ...]
    missing: tuple[MissingInfo, ...]
    risks: tuple[Risk, ...]
    assumptions_used: tuple[str, ...]


# ---------------------------------------------------------------------------
# Balance diario
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DayResult:
    water: float
    eta: float
    drainage: float
    ks: float


def bucket_step(prev: float, eff_rain: float, etc: float, awc: float, p: float) -> DayResult:
    """Un día del balde: ETa = Ks·ETc (FAO-56 cap. 8), acotado a [0, AU], excedente drenado."""
    if awc <= 0:
        return DayResult(water=0.0, eta=0.0, drainage=eff_rain, ks=0.0)
    depletion = awc - prev
    raw = p * awc
    ks = 1.0 if depletion <= raw else max(0.0, prev / ((1.0 - p) * awc))
    eta = ks * etc
    water = prev + eff_rain - eta
    drainage = 0.0
    if water > awc:
        drainage = water - awc
        water = awc
    if water < 0:
        eta = eta + water
        water = 0.0
    return DayResult(water=water, eta=eta, drainage=drainage, ks=ks)


def kc_for_day(kc: tuple[float, float, float], fractions: tuple[float, ...], t: float) -> float:
    """Kc en la fracción t ∈ [0, 1] del ciclo: ini, rampa, mid, rampa a end."""
    f_ini, f_dev, f_mid, _ = fractions
    k_ini, k_mid, k_end = kc
    if t <= f_ini:
        return k_ini
    if t <= f_ini + f_dev:
        return k_ini + (k_mid - k_ini) * (t - f_ini) / f_dev
    if t <= f_ini + f_dev + f_mid:
        return k_mid
    rest = 1.0 - (f_ini + f_dev + f_mid)
    return k_mid + (k_end - k_mid) * min(1.0, (t - f_ini - f_dev - f_mid) / rest)


def _date(year: int, spec: tuple[int, int, int]) -> date:
    return date(year + spec[0], spec[1], spec[2])


@dataclass(frozen=True)
class CropWindow:
    crop: Crop
    start: date
    end: date  # último día en el lote (cosecha o terminación)


def campaign_windows(campaign: Campaign, year: int, cfg: WaterConfig) -> list[CropWindow]:
    windows: list[CropWindow] = []
    summer_sow: date | None = None
    if campaign.summer is not None:
        cd = cfg.calendar[campaign.summer]
        summer_sow = _date(year, cd.sow)
        windows.append(CropWindow(campaign.summer, summer_sow, _date(year, cd.harvest)))
    if campaign.winter is not None:
        cd = cfg.calendar[campaign.winter]
        start = _date(year, cd.sow)
        end = _date(year, cd.harvest)
        if CROP_INFO[campaign.winter].kind is CropKind.SERVICE and summer_sow is not None:
            end = summer_sow - timedelta(days=cfg.cover_termination_days)
        windows.insert(0, CropWindow(campaign.winter, start, end))
    return windows


@dataclass
class CropAcc:
    eta: list[float] = field(default_factory=list)
    etc: list[float] = field(default_factory=list)
    eta_month: dict[int, list[float]] = field(default_factory=dict)
    etc_month: dict[int, list[float]] = field(default_factory=dict)


@dataclass
class CampaignSim:
    crops: dict[Crop, CropAcc]
    water_at_summer_sowing: float | None
    rain_source: Dataset


def _series_value(series: tuple[float, ...], start: date, d: date) -> float:
    return series[(d - start).days]


def simulate_campaign(
    weather: ScenarioWeather,
    windows: list[CropWindow],
    period: tuple[date, date],
    initial_water: float,
    awc: float,
    cfg: WaterConfig,
    rain: tuple[float, ...],
    rain_source: Dataset,
    summer_sow: date | None,
) -> CampaignSim:
    accs = {w.crop: CropAcc() for w in windows}
    water = initial_water
    water_at_sow: float | None = None
    d = period[0]
    while d <= period[1]:
        active = next((w for w in windows if w.start <= d <= w.end), None)
        if active is not None:
            span = max(1, (active.end - active.start).days)
            t = (d - active.start).days / span
            kc = kc_for_day(cfg.kc[active.crop], cfg.stage_fractions, t)
            p = cfg.p.get(active.crop.value, 0.5)
        else:
            kc = cfg.fallow_kc
            p = cfg.p.get("FALLOW", 0.5)
        if summer_sow is not None and d == summer_sow:
            water_at_sow = water
        et0 = _series_value(weather.et0_mm, weather.start_date, d)
        eff = cfg.rain_fraction * _series_value(rain, weather.start_date, d)
        etc = kc * et0
        step = bucket_step(water, eff, etc, awc, p)
        water = step.water
        if active is not None:
            acc = accs[active.crop]
            acc.eta.append(step.eta)
            acc.etc.append(etc)
            acc.eta_month.setdefault(d.month, []).append(step.eta)
            acc.etc_month.setdefault(d.month, []).append(etc)
        d += timedelta(days=1)
    return CampaignSim(crops=accs, water_at_summer_sowing=water_at_sow, rain_source=rain_source)


def stress_index(eta: list[float], etc: list[float]) -> float:
    total_etc = math.fsum(etc)
    if total_etc <= 0:
        return 0.0
    return max(0.0, 1.0 - math.fsum(eta) / total_etc)


# ---------------------------------------------------------------------------
# Suelo e inicio
# ---------------------------------------------------------------------------


def _derived(method: str, *inputs: str) -> DerivedProvenance:
    return DerivedProvenance(method=method, derived_from=tuple(inputs) or ("rastrojo",))


def _is_soilgrids(pv: PValue) -> bool:
    prov = pv.provenance
    if isinstance(prov, ObservedProvenance):
        return prov.source.dataset is Dataset.SOILGRIDS
    if isinstance(prov, DerivedProvenance):
        return any("SOILGRIDS" in x for x in prov.derived_from)
    return False


def _theta(soil: Soil, cfg: WaterConfig) -> tuple[float, float, str]:
    key = soil.texture.value.value if soil.texture is not None else "GENERIC"
    if key not in cfg.theta:
        key = "GENERIC"
    fc, wp = cfg.theta[key]
    return fc, wp, key


def resolve_awc(soil: Soil, cfg: WaterConfig) -> tuple[PValue, list[Reason], list[MissingInfo]]:
    reasons: list[Reason] = []
    missing: list[MissingInfo] = []
    if soil.available_water_mm is not None:
        awc = soil.available_water_mm
        if _is_soilgrids(awc):
            reasons.append(
                Reason(code=ReasonCode.SOIL_AWC_FROM_SOILGRIDS, assumption_ids=("A-WAT-17",))
            )
            missing.append(
                MissingInfo(
                    item="agua útil del perfil medida o de carta de suelo",
                    why_it_matters=(
                        "El agua útil viene de SoilGrids, un dato modelado global de 250 m que no "
                        "reemplaza la carta de suelo INTA del lote."
                    ),
                    how_to_get="Carta de suelo INTA (GeoINTA) o análisis de suelo del lote.",
                )
            )
        return awc, reasons, missing
    reasons.append(
        Reason(code=ReasonCode.SOIL_AWC_ASSUMED, assumption_ids=("A-WAT-13", "A-WAT-14"))
    )
    missing.append(
        MissingInfo(
            item="agua útil del perfil",
            why_it_matters="Define cuánta agua puede guardar el suelo para el cultivo siguiente.",
            how_to_get="Carta de suelo INTA (GeoINTA), análisis de suelo o dato del agrónomo.",
        )
    )
    if soil.texture is not None and soil.texture.value.value in cfg.theta:
        fc, wp, key = _theta(soil, cfg)
        value = (fc - wp) * cfg.awc_reference_depth_m * 1000.0
        prov = _derived(
            f"(θcc − θmp) × profundidad de referencia, textura {key}", "A-WAT-13", "A-WAT-14"
        )
        return PValue(value=round(value, 6), unit="mm", provenance=prov), reasons, missing
    return (
        PValue(
            value=cfg.awc_generic_mm,
            unit="mm",
            provenance=AssumptionProvenance(assumption_id="A-WAT-14"),
        ),
        reasons,
        missing,
    )


def resolve_initial(
    soil: Soil, inputs: WaterInputs, awc: PValue, cfg: WaterConfig
) -> tuple[PValue, list[Reason], list[MissingInfo]]:
    smap = inputs.smap_initial_rootzone
    if smap is None:
        value = cfg.fallback_initial_fraction * awc.value
        return (
            PValue(
                value=value,
                unit="mm",
                provenance=_derived("fracción supuesta × agua útil", "A-WAT-12"),
            ),
            [Reason(code=ReasonCode.INITIAL_MOISTURE_ASSUMED, assumption_ids=("A-WAT-12",))],
            [
                MissingInfo(
                    item="humedad inicial del perfil (SMAP L4)",
                    why_it_matters="El agua guardada hoy define si conviene un doble cultivo o un servicio.",
                    how_to_get="Bajar SMAP L4 sm_rootzone de la fecha de referencia o medir con sonda.",
                )
            ],
        )
    fc, wp, _ = _theta(soil, cfg)
    frac = min(1.0, max(0.0, (smap.value - wp) / (fc - wp)))
    prov = _derived("(θ SMAP − θmp)/(θcc − θmp) × agua útil", "SMAP_L4:sm_rootzone", "A-WAT-13")
    return PValue(value=round(frac * awc.value, 6), unit="mm", provenance=prov), [], []


# ---------------------------------------------------------------------------
# Evaluación
# ---------------------------------------------------------------------------


def _level(freq: float, cfg: WaterConfig) -> Severity:
    if freq >= cfg.level_high:
        return Severity.HIGH
    if freq >= cfg.level_medium:
        return Severity.MEDIUM
    return Severity.LOW


def _covers(weather: ScenarioWeather, period: tuple[date, date]) -> bool:
    end = weather.start_date + timedelta(days=len(weather.rain_mm) - 1)
    return weather.start_date <= period[0] and end >= period[1]


def _period(windows: list[CropWindow], year: int, cfg: WaterConfig) -> tuple[date, date]:
    start = date(year, cfg.winter_start[0], cfg.winter_start[1])
    start = min([start] + [w.start for w in windows])
    end = max(w.end for w in windows)
    return start, end


def _rain_for(
    weather: ScenarioWeather, period: tuple[date, date]
) -> tuple[tuple[float, ...], Dataset, float, float | None]:
    """Regla conservadora A-WAT-16: la serie con menor lluvia de campaña si ambas están completas."""
    i0 = (period[0] - weather.start_date).days
    i1 = (period[1] - weather.start_date).days + 1
    power_sum = math.fsum(weather.rain_mm[i0:i1])
    if weather.imerg_rain_mm is None:
        return weather.rain_mm, Dataset.NASA_POWER, power_sum, None
    imerg_sum = math.fsum(weather.imerg_rain_mm[i0:i1])
    if imerg_sum < power_sum:
        return weather.imerg_rain_mm, Dataset.GPM_IMERG, power_sum, imerg_sum
    return weather.rain_mm, Dataset.NASA_POWER, power_sum, imerg_sum


def _weighted(values: list[tuple[float, float]]) -> float:
    total_w = math.fsum(w for _, w in values)
    return math.fsum(v * w for v, w in values) / total_w if total_w > 0 else 0.0


def _class_ranges(
    scen: list[ScenarioWater], weights: dict[int, float], deficits: dict[int, float]
) -> tuple[ClassRange, ...]:
    out: list[ClassRange] = []
    prov = _derived("rango por clase anual de escenarios válidos", "rastrojo.water")
    for cls in YearClass:
        rows = [s for s in scen if s.annual_class is cls and not s.excluded]
        if not rows:
            out.append(
                ClassRange(
                    year_class=cls, count=0, empty_reason="sin escenarios válidos en la clase"
                )
            )
            continue
        defs = [(deficits[s.campaign_start_year], weights[s.campaign_start_year]) for s in rows]
        sow = [
            (s.water_at_summer_sowing.value, weights[s.campaign_start_year])
            for s in rows
            if s.water_at_summer_sowing is not None
        ]

        def pv(v: float) -> PValue:
            return PValue(value=round(v, 6), unit="mm", provenance=prov)

        out.append(
            ClassRange(
                year_class=cls,
                count=len(rows),
                deficit_min=pv(min(v for v, _ in defs)),
                deficit_mean=pv(_weighted(defs)),
                deficit_max=pv(max(v for v, _ in defs)),
                sowing_water_min=pv(min(v for v, _ in sow)) if sow else None,
                sowing_water_mean=pv(_weighted(sow)) if sow else None,
                sowing_water_max=pv(max(v for v, _ in sow)) if sow else None,
            )
        )
    return tuple(out)


@dataclass
class _EventAcc:
    in_field: set[int] = field(default_factory=set)
    years: dict[int, set[int]] = field(default_factory=dict)  # mes -> años con evento
    valid_years: set[int] = field(default_factory=set)


def _extreme_threshold(inputs: WaterInputs, percentile: float) -> float | None:
    days = sorted(
        v for w in inputs.weather if w.imerg_rain_mm is not None for v in w.imerg_rain_mm if v > 0
    )
    if not days:
        return None
    rank = max(1, math.ceil(percentile * len(days)))  # rango más cercano
    return days[rank - 1]


def evaluate_rotation(
    rotation: Rotation,
    soil: Soil,
    scenarios: tuple[ClimateScenario, ...],
    inputs: WaterInputs,
    resolved: dict[str, ResolvedAssumption],
) -> WaterAssessment:
    cfg = water_config(resolved)
    awc, reasons, missing = resolve_awc(soil, cfg)
    initial, r2, m2 = resolve_initial(soil, inputs, awc, cfg)
    reasons += r2
    missing += m2
    weather_by_year = {w.campaign_start_year: w for w in inputs.weather}
    ordered = sorted(scenarios, key=lambda s: s.campaign_start_year)
    extreme_thr = _extreme_threshold(inputs, cfg.extreme_percentile)

    campaigns: list[CampaignWater] = []
    crop_status: list[CropScenarioStatus] = []
    events: dict[tuple[Crop, str], _EventAcc] = {}
    risks: list[Risk] = []
    frost_years: dict[Crop, list[tuple[int, float]]] = {}
    sources_used: set[Dataset] = set()

    for idx, campaign in enumerate(rotation.campaigns):
        is_double_or_cover = campaign.is_double_crop or campaign.has_cover_crop
        scen_rows: list[ScenarioWater] = []
        deficits: dict[int, float] = {}
        valid_weights: dict[int, float] = {}
        severe_years: list[int] = []
        low_recharge_years: list[tuple[int, str]] = []
        excluded_years: list[int] = []
        cover_costs: list[tuple[float, int]] = []

        for sc in ordered:
            y = sc.campaign_start_year
            windows = campaign_windows(campaign, y, cfg)
            period = _period(windows, y, cfg)
            w = weather_by_year.get(y)
            if w is None or not _covers(w, period):
                excluded_years.append(y)
                scen_rows.append(
                    ScenarioWater(
                        campaign_start_year=y, annual_class=sc.annual_class, excluded=True
                    )
                )
                for c in (campaign.winter, campaign.summer):
                    if c is not None:
                        crop_status.append(
                            CropScenarioStatus(
                                crop=c,
                                campaign_index=idx,
                                campaign_start_year=y,
                                status=WaterFeasibility.UNKNOWN,
                            )
                        )
                continue
            rain, source, _, _ = _rain_for(w, period)
            sources_used.add(source)
            summer_sow = next((cw.start for cw in windows if cw.crop is campaign.summer), None)
            sim = simulate_campaign(
                w, windows, period, initial.value, awc.value, cfg, rain, source, summer_sow
            )
            crops_out: list[CropScenarioWater] = []
            any_severe = False
            total_deficit = 0.0
            frac: float | None = None
            if sim.water_at_summer_sowing is not None and awc.value > 0:
                frac = sim.water_at_summer_sowing / awc.value
            for cw in windows:
                acc = sim.crops[cw.crop]
                si = stress_index(acc.eta, acc.etc)
                deficit = math.fsum(acc.etc) - math.fsum(acc.eta)
                label: StressLabel = (
                    "SEVERE" if si > cfg.severe else ("MODERATE" if si > cfg.moderate else "NONE")
                )
                is_cash = CROP_INFO[cw.crop].kind is CropKind.CASH
                if is_cash:
                    total_deficit += deficit
                    if label == "SEVERE":
                        any_severe = True
                if label == "SEVERE":
                    status = WaterFeasibility.NOT_FEASIBLE
                elif label == "MODERATE" or (
                    cw.crop is campaign.summer
                    and is_double_or_cover
                    and frac is not None
                    and frac < cfg.min_recharge_fraction
                ):
                    status = WaterFeasibility.RISKY
                else:
                    status = WaterFeasibility.FEASIBLE
                prov = _derived(
                    "balance diario tipo balde FAO-56",
                    f"{source.value}:lluvia",
                    "ET0:FAO-56",
                    "A-WAT-01",
                    "A-WAT-02",
                    "A-WAT-03",
                )
                crops_out.append(
                    CropScenarioWater(
                        crop=cw.crop,
                        stress_index=PValue(value=round(si, 6), unit="index", provenance=prov),
                        deficit=PValue(value=round(deficit, 6), unit="mm", provenance=prov),
                        label=label,
                        status=status,
                    )
                )
                crop_status.append(
                    CropScenarioStatus(
                        crop=cw.crop, campaign_index=idx, campaign_start_year=y, status=status
                    )
                )
                # Calendario: déficit mensual, helada, calor y lluvia extrema.
                months_in = set(acc.etc_month)
                for ev in ("WATER_DEFICIT", "FROST", "HEAT_STRESS", "EXTREME_RAIN"):
                    ev_acc = events.setdefault((cw.crop, ev), _EventAcc())
                    ev_acc.in_field |= months_in
                    if ev != "EXTREME_RAIN" or w.imerg_rain_mm is not None:
                        ev_acc.valid_years.add(y)
                for m in months_in:
                    if stress_index(acc.eta_month[m], acc.etc_month[m]) > cfg.moderate:
                        events[(cw.crop, "WATER_DEFICIT")].years.setdefault(m, set()).add(y)
                fw = cfg.frost_windows.get(cw.crop)
                frosted = False
                if fw is not None:
                    for dd in range(fw[0], fw[1] + 1):
                        day = cw.start + timedelta(days=dd)
                        if day > cw.end:
                            break
                        if _series_value(w.t2m_min_c, w.start_date, day) <= cfg.frost_threshold:
                            events[(cw.crop, "FROST")].years.setdefault(day.month, set()).add(y)
                            frosted = True
                    frost_years.setdefault(cw.crop, []).append((y, 1.0 if frosted else 0.0))
                hw = cfg.flowering_windows.get(cw.crop)
                if hw is not None:
                    for dd in range(hw[0], hw[1] + 1):
                        day = cw.start + timedelta(days=dd)
                        if day > cw.end:
                            break
                        if _series_value(w.t2m_max_c, w.start_date, day) >= cfg.heat_threshold:
                            events[(cw.crop, "HEAT_STRESS")].years.setdefault(day.month, set()).add(
                                y
                            )
                if extreme_thr is not None and w.imerg_rain_mm is not None and is_cash:
                    day = cw.start
                    while day <= cw.end:
                        if _series_value(w.imerg_rain_mm, w.start_date, day) >= extreme_thr:
                            events[(cw.crop, "EXTREME_RAIN")].years.setdefault(
                                day.month, set()
                            ).add(y)
                        day += timedelta(days=1)

            fallow_pv: PValue | None = None
            if campaign.has_cover_crop and summer_sow is not None:
                fallow_windows = [cw for cw in windows if cw.crop is campaign.summer]
                fsim = simulate_campaign(
                    w,
                    fallow_windows,
                    period,
                    initial.value,
                    awc.value,
                    cfg,
                    rain,
                    source,
                    summer_sow,
                )
                if (
                    fsim.water_at_summer_sowing is not None
                    and sim.water_at_summer_sowing is not None
                ):
                    fallow_pv = PValue(
                        value=round(fsim.water_at_summer_sowing, 6),
                        unit="mm",
                        provenance=_derived(
                            "balance con barbecho en lugar del servicio", "rastrojo.water"
                        ),
                    )
                    cover_costs.append(
                        (fsim.water_at_summer_sowing - sim.water_at_summer_sowing, y)
                    )
            if any_severe:
                severe_years.append(y)
            if is_double_or_cover and frac is not None and frac < cfg.min_recharge_fraction:
                low_recharge_years.append((y, sc.annual_class.value))
            deficits[y] = total_deficit
            valid_weights[y] = sc.weight
            sow_pv = None
            if sim.water_at_summer_sowing is not None:
                sow_pv = PValue(
                    value=round(sim.water_at_summer_sowing, 6),
                    unit="mm",
                    provenance=_derived(
                        "agua útil al día de siembra del cultivo de verano", "rastrojo.water"
                    ),
                )
            scen_rows.append(
                ScenarioWater(
                    campaign_start_year=y,
                    annual_class=sc.annual_class,
                    excluded=False,
                    rain_source=source,
                    crops=tuple(crops_out),
                    water_at_summer_sowing=sow_pv,
                    fraction_at_summer_sowing=round(frac, 6) if frac is not None else None,
                    fallow_water_at_summer_sowing=fallow_pv,
                )
            )

        c_reasons: list[Reason] = []
        n_valid = len(valid_weights)
        total_w = math.fsum(valid_weights.values())
        weights = {y: (v / total_w if total_w > 0 else 0.0) for y, v in valid_weights.items()}
        if excluded_years:
            c_reasons.append(
                Reason(code=ReasonCode.MISSING_WEATHER, params={"years": excluded_years})
            )
            c_reasons.append(
                Reason(
                    code=ReasonCode.SCENARIOS_EXCLUDED,
                    params={"valid": n_valid, "excluded": len(excluded_years)},
                )
            )
        severe_freq_pv: PValue | None = None
        if n_valid < cfg.min_scenarios:
            status = WaterFeasibility.UNKNOWN
            c_reasons.append(
                Reason(
                    code=ReasonCode.INSUFFICIENT_SCENARIOS,
                    params={"valid": n_valid, "required": cfg.min_scenarios},
                    assumption_ids=("A-CLI-03",),
                )
            )
            missing.append(
                MissingInfo(
                    item=f"clima diario completo (campaña {idx + 1})",
                    why_it_matters=f"Hay {n_valid} años válidos y hacen falta {cfg.min_scenarios} para decidir sobre el agua.",
                    how_to_get="Completar la descarga de NASA POWER para el lote o revisar los años con huecos.",
                )
            )
        else:
            severe_freq = math.fsum(weights[y] for y in severe_years)
            severe_freq_pv = PValue(
                value=round(severe_freq, 6),
                unit="fraction",
                provenance=_derived("frecuencia ponderada de años SEVERE", "A-WAT-05"),
            )
            if severe_freq > cfg.not_feasible_freq:
                status = WaterFeasibility.NOT_FEASIBLE
            elif severe_freq > cfg.feasible_max_freq:
                status = WaterFeasibility.RISKY
            else:
                status = WaterFeasibility.FEASIBLE
            if severe_years:
                c_reasons.append(
                    Reason(
                        code=ReasonCode.SEVERE_STRESS_FREQUENT,
                        params={
                            "years": severe_years,
                            "count": len(severe_years),
                            "total": n_valid,
                            "frequency": round(severe_freq, 6),
                        },
                        assumption_ids=("A-WAT-05", "A-WAT-06", "A-WAT-07"),
                    )
                )
            low_freq = math.fsum(weights[y] for y, _ in low_recharge_years)
            if is_double_or_cover and low_freq > cfg.feasible_max_freq:
                status = worst([status, WaterFeasibility.RISKY])
                c_reasons.append(
                    Reason(
                        code=ReasonCode.PROFILE_NOT_RECHARGED_AT_SOWING,
                        params={
                            "years": [y for y, _ in low_recharge_years],
                            "classes": [c for _, c in low_recharge_years],
                            "frequency": round(low_freq, 6),
                        },
                        assumption_ids=("A-WAT-08", "A-WAT-06"),
                    )
                )
            tws = inputs.grace_tws_anomaly
            if (
                status is WaterFeasibility.FEASIBLE
                and tws is not None
                and tws.value < cfg.grace_threshold_mm
            ):
                status = WaterFeasibility.RISKY
                c_reasons.append(
                    Reason(
                        code=ReasonCode.GRACE_REGIONAL_DEFICIT,
                        params={"tws_mm": tws.value},
                        assumption_ids=("A-WAT-10",),
                    )
                )
        if any(s.rain_source is Dataset.GPM_IMERG for s in scen_rows):
            c_reasons.append(
                Reason(
                    code=ReasonCode.CONSERVATIVE_RAIN_SOURCE,
                    params={
                        "years": [
                            s.campaign_start_year
                            for s in scen_rows
                            if s.rain_source is Dataset.GPM_IMERG
                        ]
                    },
                    assumption_ids=("A-WAT-16",),
                )
            )
        cover_cost_pv = None
        if cover_costs:
            mean_cost = _weighted([(cost, weights.get(y, 0.0)) for cost, y in cover_costs])
            cover_cost_pv = PValue(
                value=round(mean_cost, 6),
                unit="mm",
                provenance=_derived(
                    "agua a la siembra con barbecho menos con servicio, promedio ponderado",
                    "rastrojo.water",
                ),
            )
        campaigns.append(
            CampaignWater(
                campaign_index=idx,
                status=status,
                reasons=tuple(c_reasons),
                valid_scenarios=n_valid,
                severe_frequency=severe_freq_pv,
                scenarios=tuple(scen_rows),
                ranges=_class_ranges(scen_rows, weights, deficits),
                cover_water_cost=cover_cost_pv,
            )
        )

    status = worst([c.status for c in campaigns])
    determining = [c.campaign_index for c in campaigns if c.status is status]
    reasons.append(
        Reason(code=ReasonCode.DETERMINED_BY_CAMPAIGN, params={"campaigns": determining})
    )

    if soil.water_table_depth_m is not None:
        lo, hi = cfg.water_table_range
        if lo <= soil.water_table_depth_m.value <= hi:
            reasons.append(
                Reason(
                    code=ReasonCode.SHALLOW_WATER_TABLE_MITIGATES,
                    params={"depth_m": soil.water_table_depth_m.value},
                    assumption_ids=("A-WAT-11",),
                )
            )
    else:
        missing.append(
            MissingInfo(
                item="profundidad de napa",
                why_it_matters="Una napa somera (rango del supuesto A-WAT-11) puede aportar agua al doble cultivo en años secos.",
                how_to_get="Freatímetro en el lote o registro de napas de la zona (INTA, cooperativa).",
            )
        )
    if inputs.grace_tws_anomaly is None:
        missing.append(
            MissingInfo(
                item="anomalía de agua total regional (GRACE-FO)",
                why_it_matters="Da contexto de si la región viene con reservas bajas.",
                how_to_get="Mascons GRACE-FO de JPL/CSR vía Earthdata.",
            )
        )
    if extreme_thr is None:
        missing.append(
            MissingInfo(
                item="lluvia diaria IMERG",
                why_it_matters="Sin IMERG no se puede marcar el riesgo de lluvia extrema en el calendario.",
                how_to_get="Bajar GPM IMERG Final diario para el lote vía Earthdata.",
            )
        )

    for crop, rows in sorted(frost_years.items(), key=lambda kv: kv[0].value):
        n = len(rows)
        hits = [y for y, v in rows if v > 0]
        freq = len(hits) / n if n else 0.0
        if hits:
            risks.append(
                Risk(
                    risk_type=RiskType.FROST,
                    severity=_level(freq, cfg),
                    description=(
                        f"{CROP_INFO[crop].label_es}: helada en la ventana sensible en {len(hits)} de {n} "
                        "años (T2M_MIN es temperatura a 2 m de una celda regional, no del lote)."
                    ),
                    basis="EVIDENCE",
                    reference="NASA_POWER:T2M_MIN",
                )
            )

    vulnerability: list[VulnerabilityEntry] = []
    cal_prov = _derived(
        "frecuencia de años con el evento por mes", "NASA_POWER", "A-CLI-05", "A-CLI-07", "A-WAT-04"
    )
    for (crop, ev), ev_acc in sorted(events.items(), key=lambda kv: (kv[0][0].value, kv[0][1])):
        freqs: list[float] = []
        inside: list[bool] = []
        levels: list[Severity | None] = []
        years: list[tuple[int, ...]] = []
        for m in range(1, 13):
            if m in ev_acc.in_field:
                ys = tuple(sorted(ev_acc.years.get(m, set())))
                f = round(len(ys) / max(1, len(ev_acc.valid_years)), 6)
                freqs.append(f)
                inside.append(True)
                levels.append(_level(f, cfg))
                years.append(ys)
            else:
                freqs.append(0.0)
                inside.append(False)
                levels.append(None)
                years.append(())
        if ev == "EXTREME_RAIN" and extreme_thr is None:
            continue
        vulnerability.append(
            VulnerabilityEntry(
                crop=crop,
                event=ev,
                frequency_by_month=tuple(freqs),
                in_field_by_month=tuple(inside),
                level_by_month=tuple(levels),
                years_by_month=tuple(years),
                provenance=cal_prov,
            )
        )

    evidence = _evidence(inputs, initial, sources_used)
    return WaterAssessment(
        rotation_id=rotation.rotation_id,
        status=status,
        reasons=tuple(reasons),
        awc=awc,
        initial_water=initial,
        campaigns=tuple(campaigns),
        crop_status=tuple(crop_status),
        vulnerability=tuple(vulnerability),
        evidence=evidence,
        missing=tuple(missing),
        risks=tuple(risks),
        assumptions_used=WATER_ASSUMPTIONS,
    )


def _evidence(inputs: WaterInputs, initial: PValue, sources: set[Dataset]) -> tuple[Evidence, ...]:
    out: list[Evidence] = []
    first = min(inputs.weather, key=lambda w: w.campaign_start_year)
    last = max(inputs.weather, key=lambda w: w.campaign_start_year)
    period = Period(
        start=first.start_date,
        end=last.start_date + timedelta(days=len(last.et0_mm) - 1),
    )
    et0_vals = [v for w in inputs.weather for v in w.et0_mm]
    mean_et0 = math.fsum(et0_vals) / len(et0_vals)
    out.append(
        Evidence(
            dataset=Dataset.NASA_POWER,
            variable="ET0 (FAO-56 Penman-Monteith desde POWER)",
            period=period,
            value=PValue(
                value=round(mean_et0, 6),
                unit="mm/day",
                provenance=_derived("media de ET0 diaria", "NASA_POWER", "ET0:FAO-56"),
            ),
            interpretation="Demanda de agua de la atmósfera: cuánto evaporaría un cultivo de referencia por día.",
        )
    )
    smap = inputs.smap_initial_rootzone
    if smap is not None and isinstance(smap.provenance, ObservedProvenance):
        out.append(
            Evidence(
                dataset=Dataset.SMAP_L4,
                variable="sm_rootzone",
                period=smap.provenance.source.period,
                value=smap,
                interpretation=(
                    f"Humedad de la zona de raíces (celda de ~9 km, modelo asimilado). Equivale a "
                    f"{initial.value:.1f} mm de agua útil al inicio."
                ),
            )
        )
    tws = inputs.grace_tws_anomaly
    if tws is not None and isinstance(tws.provenance, ObservedProvenance):
        out.append(
            Evidence(
                dataset=Dataset.GRACE_FO,
                variable="anomalía de agua total (TWS)",
                period=tws.provenance.source.period,
                value=tws,
                interpretation="Señal regional de ~300 km: contexto de reservas de la región, no del lote.",
            )
        )
    if Dataset.GPM_IMERG in sources:
        out.append(
            Evidence(
                dataset=Dataset.GPM_IMERG,
                variable="precipitación diaria (regla conservadora A-WAT-16)",
                period=period,
                value=PValue(
                    value=1,
                    unit="count",
                    provenance=_derived("años donde IMERG fue más seca que POWER", "A-WAT-16"),
                ),
                interpretation="En algunos años el balance usó IMERG porque registró menos lluvia que POWER.",
            )
        )
    return tuple(out)
