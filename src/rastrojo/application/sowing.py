"""¿Me conviene sembrar? Decisión en lenguaje llano sobre la salida del motor.

Compara la rotación que el motor pone primera para el actor contra dos alternativas sin cultivo:
alquilar el campo (o, para el arrendatario, no renovar el arriendo) y dejarlo en barbecho.
No calcula márgenes nuevos: usa los márgenes anuales que ya devuelve el motor por campaña
histórica y valores de alternativas que son supuestos (A-ECO-05, A-ECO-06) o datos del usuario.
Determinista y sin red, como el motor.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.domain.base import DomainModel
from rastrojo.domain.crops import Crop
from rastrojo.domain.economics import EconomicParameters
from rastrojo.domain.engine_io import EngineOutput
from rastrojo.domain.provenance import (
    AssumptionProvenance,
    DerivedProvenance,
    PValue,
    UserInputProvenance,
)
from rastrojo.domain.results import RotationResult, WaterFeasibility
from rastrojo.engine.economics import net_price

Verdict = Literal["SOW", "SOW_WITH_RISK", "RENT_BETTER", "DONT_SOW"]
RENT_QQ_ID = "A-ECO-05"
FALLOW_ID = "A-ECO-06"
RISK_SHARE_ID = "A-ACT-10"
QQ_TO_T_ID = "A-ECO-04"


class SowingDecision(DomainModel):
    """Respuesta a "¿me conviene sembrar?" (o, para el arrendatario, "¿sigo arrendando?")."""

    verdict: Verdict
    actor: str
    rotation_id: str | None = None
    expected_margin: PValue | None = Field(
        default=None, description="Margen bruto anual esperado de la rotación (sin arriendo)"
    )
    rent: PValue = Field(description="Arrendamiento anual del lote en USD/ha")
    fallow_cost: PValue = Field(description="Costo anual de barbecho en USD/ha")
    vs_rent: PValue | None = Field(
        default=None, description="Margen esperado menos arrendamiento (USD/ha por año)"
    )
    vs_fallow: PValue | None = Field(
        default=None,
        description="Margen esperado más el costo de barbecho evitado (USD/ha por año)",
    )
    breakeven_rent_qq: PValue | None = Field(
        default=None,
        description="Arriendo en qq soja/ha con el que sembrar y alquilar dejan lo mismo",
    )
    rent_qq: float = Field(ge=0, description="Arriendo usado, en qq soja/ha")
    campaigns_below_rent: int = 0
    campaigns_below_fallow: int = 0
    campaigns_total: int = 0
    water: WaterFeasibility | None = None
    headline: str
    reasons: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()


def _fmt(v: float) -> str:
    """Entero con separador de miles argentino (1.353)."""
    return f"{round(v):,}".replace(",", ".")


def usd_per_qq(registry: AssumptionRegistry, economics: EconomicParameters) -> float:
    soy = economics.for_crop(Crop.SOY_1ST)
    if soy is None or soy.price is None or soy.export_tax is None:
        raise ValueError("falta el precio de soja para valuar el arrendamiento")
    return float(registry.value(QQ_TO_T_ID)) * net_price(soy)


def rent_usd_ha(
    registry: AssumptionRegistry,
    economics: EconomicParameters,
    rent_qq_ha: float | None = None,
) -> PValue:
    """Arrendamiento en USD/ha: quintales de soja × t/qq × precio neto de soja (como el motor)."""
    soy = economics.for_crop(Crop.SOY_1ST)
    if soy is None or soy.price is None or soy.export_tax is None:
        raise ValueError("falta el precio de soja para valuar el arrendamiento")
    qq = float(registry.value(RENT_QQ_ID)) if rent_qq_ha is None else rent_qq_ha
    usd = qq * float(registry.value(QQ_TO_T_ID)) * net_price(soy)
    source = "usuario" if rent_qq_ha is not None else RENT_QQ_ID
    return PValue(
        value=round(usd, 6),
        unit="USD/ha",
        provenance=DerivedProvenance(
            method=f"{qq:g} qq soja/ha × t/qq × precio neto de soja",
            derived_from=(source, QQ_TO_T_ID, "A-DEMO-02", "A-DEMO-03"),
        ),
    )


def fallow_cost_usd_ha(registry: AssumptionRegistry, override: float | None = None) -> PValue:
    if override is not None:
        return PValue(value=override, unit="USD/ha", provenance=UserInputProvenance())
    return PValue(
        value=float(registry.value(FALLOW_ID)),
        unit="USD/ha",
        provenance=AssumptionProvenance(assumption_id=FALLOW_ID),
    )


def _top(output: EngineOutput) -> RotationResult | None:
    eligible = [r for r in output.results if r.eligible and r.expected_annual_margin is not None]
    return min(eligible, key=lambda r: r.rank) if eligible else None


def decide(
    output: EngineOutput,
    names: dict[str, str],
    rent: PValue,
    fallow_cost: PValue,
    max_share_below_rent: float,
    usd_per_qq: float,
) -> SowingDecision:
    rent_qq = rent.value / usd_per_qq if usd_per_qq > 0 else 0.0
    actor = output.profile_id
    tenant = actor == "TENANT"
    alt = "devolver el campo y no pagar el arriendo" if tenant else "alquilar el campo"
    short = "devolver el campo" if tenant else "alquilarlo"
    used = (RENT_QQ_ID, QQ_TO_T_ID, FALLOW_ID, RISK_SHARE_ID)
    top = _top(output)
    if top is None:
        return SowingDecision(
            verdict="DONT_SOW",
            actor=actor,
            rent=rent,
            rent_qq=round(rent_qq, 6),
            fallow_cost=fallow_cost,
            headline=(
                "Con estas condiciones no conviene seguir arrendando: ninguna rotación es elegible."
                if tenant
                else "Con estas condiciones no conviene sembrar: ninguna rotación es elegible."
            ),
            reasons=(f"Mejor alternativa: {alt}.",),
            assumptions=used,
        )

    name = names.get(top.rotation_id, top.rotation_id)
    assert top.expected_annual_margin is not None
    margin = top.expected_annual_margin.value
    annual = [a.margin.value for a in top.annual_margins]
    n = len(annual)
    below_rent = sum(1 for v in annual if v < rent.value)
    below_fallow = sum(1 for v in annual if v < -fallow_cost.value)
    d_rent = margin - rent.value
    d_fallow = margin + fallow_cost.value
    prov = DerivedProvenance(
        method="margen anual esperado de la rotación frente a la alternativa sin cultivo",
        derived_from=("economics", RENT_QQ_ID, FALLOW_ID),
    )
    risky_water = top.water_feasibility in (WaterFeasibility.RISKY, WaterFeasibility.NOT_FEASIBLE)
    share = below_rent / n if n else 0.0

    reasons: list[str] = []
    if d_fallow <= 0:
        verdict: Verdict = "DONT_SOW"
        headline = (
            f"No conviene seguir arrendando: {name}, la mejor opción, deja menos que el barbecho."
            if tenant
            else f"No conviene sembrar: {name}, la mejor opción, deja menos que el barbecho."
        )
    elif d_rent <= 0:
        verdict = "RENT_BETTER"
        headline = (
            f"Conviene más devolver el campo: {name} deja en promedio "
            f"{_fmt(-d_rent)} USD/ha menos que lo que cuesta el arriendo."
            if tenant
            else f"Conviene más alquilar el campo: sembrar {name} deja en promedio "
            f"{_fmt(-d_rent)} USD/ha menos por año."
        )
    elif share > max_share_below_rent or risky_water:
        verdict = "SOW_WITH_RISK"
        headline = (
            f"Sí, conviene seguir arrendando con {name}, pero con riesgo."
            if tenant
            else f"Sí, conviene sembrar {name}, pero con riesgo."
        )
    else:
        verdict = "SOW"
        headline = (
            f"Sí, conviene seguir arrendando y sembrar {name}."
            if tenant
            else f"Sí, conviene sembrar {name}."
        )

    if d_rent > 0:
        reasons.append(
            f"Deja en promedio {_fmt(d_rent)} USD/ha por año más que {alt}"
            f" (margen esperado {_fmt(margin)} USD/ha contra un arriendo de {_fmt(rent.value)} USD/ha)."
        )
    if n:
        reasons.append(
            f"En {below_rent} de {n} campañas históricas habría dejado menos que {short}."
        )
    if risky_water:
        reasons.append("En agua es riesgosa: en años secos el cultivo puede sufrir déficit.")
    if d_fallow > 0 and verdict in ("RENT_BETTER",):
        reasons.append(
            f"Igual es mejor que dejar el lote en barbecho: {_fmt(d_fallow)} USD/ha por año más."
        )
    if usd_per_qq > 0 and margin > 0:
        even = f"{margin / usd_per_qq:.1f}".replace(".", ",")
        reasons.append(f"Con un arriendo de {even} qq/ha da lo mismo sembrar que {short}.")
    if tenant:
        reasons.append("Mira solo el año que viene: el arrendatario no cobra la mejora del suelo.")

    return SowingDecision(
        verdict=verdict,
        actor=actor,
        rotation_id=top.rotation_id,
        expected_margin=top.expected_annual_margin,
        rent=rent,
        rent_qq=round(rent_qq, 6),
        breakeven_rent_qq=PValue(
            value=round(max(margin, 0.0) / usd_per_qq, 6) if usd_per_qq > 0 else 0.0,
            unit="qq/ha",
            provenance=DerivedProvenance(
                method="margen anual esperado / (t/qq × precio neto de soja)",
                derived_from=("economics", QQ_TO_T_ID, "A-DEMO-02", "A-DEMO-03"),
            ),
        ),
        fallow_cost=fallow_cost,
        vs_rent=PValue(value=round(d_rent, 6), unit="USD/ha", provenance=prov),
        vs_fallow=PValue(value=round(d_fallow, 6), unit="USD/ha", provenance=prov),
        campaigns_below_rent=below_rent,
        campaigns_below_fallow=below_fallow,
        campaigns_total=n,
        water=top.water_feasibility,
        headline=headline,
        reasons=tuple(reasons),
        assumptions=used,
    )


def sowing_decision(
    output: EngineOutput,
    names: dict[str, str],
    registry: AssumptionRegistry,
    economics: EconomicParameters,
    rent_qq_ha: float | None = None,
    fallow_cost: float | None = None,
) -> SowingDecision:
    share = float(registry.value(RISK_SHARE_ID))
    if not (0.0 <= share <= 1.0) or not math.isfinite(share):
        raise ValueError(f"{RISK_SHARE_ID} debe ser una fracción entre 0 y 1")
    return decide(
        output,
        names,
        rent_usd_ha(registry, economics, rent_qq_ha),
        fallow_cost_usd_ha(registry, fallow_cost),
        share,
        usd_per_qq(registry, economics),
    )
