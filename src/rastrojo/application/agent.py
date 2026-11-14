"""Agente "Preguntale a Rastrojo", primera iteración: cerebro determinista por reglas.

Clasifica la intención con palabras clave, extrae entidades por reglas, llama a un guion fijo
de tools de solo lectura y responde con plantillas. Sin modelo de lenguaje. El contrato
(`AskRequest`/`AskResponse`, tools y traza) es el mismo que usará el cerebro con LLM.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import (
    CATALOG,
    CATALOG_BY_ID,
    PROFILE_ASSUMPTIONS,
    actor_profile,
    build_engine_input,
    demo_economics,
)
from rastrojo.application.explanations import (
    DISCLAIMERS,
    WATER_LABEL,
    explain,
    fmt,
    load_glossary,
)
from rastrojo.application.sowing import SowingDecision, sowing_decision
from rastrojo.domain import YearClassFilter
from rastrojo.domain.engine_io import EngineOutput
from rastrojo.engine.rotation import evaluate

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
Intent = Literal[
    "sowing",
    "scope",
    "describe_situation",
    "what_if_dry",
    "why",
    "compare_actors",
    "risk",
    "water",
    "bare_soil",
    "vulnerability",
    "glossary",
    "assumptions",
    "ranking",
    "help",
]
ACTOR_LABEL = {
    "OWNER": "propietario",
    "TENANT": "arrendatario",
    "COOP": "cooperativa",
    "BANK": "banco",
}
SUGGESTIONS = (
    "¿Me conviene sembrar?",
    "¿Cuál me conviene?",
    "¿Por qué sale primera?",
    "¿Y si el año viene seco?",
    "¿Qué tan seguro es esto?",
    "¿Cuándo queda el suelo desnudo?",
)


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ConversationState(_Frozen):
    actor: str = "OWNER"
    current_rotation_id: str = "R_SOY_MONO"
    pending_profile: str | None = None
    horizon_override: int | None = None


class AskRequest(_Frozen):
    text: str = Field(min_length=1, max_length=1000)
    plot_id: str = "demo-casilda"
    state: ConversationState = ConversationState()
    channel: Literal["web", "whatsapp"] = "web"


class ToolTrace(_Frozen):
    tool: str
    params: dict[str, Any]
    input_hash: str | None = None
    engine_version: str | None = None


class AskResponse(_Frozen):
    text: str
    intent: Intent
    trace: list[ToolTrace]
    state: ConversationState
    suggestions: list[str]
    mode: Literal["scripted", "llm"] = "scripted"


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


@lru_cache(maxsize=1)
def _intents() -> list[dict[str, Any]]:
    raw = yaml.safe_load((DATA_DIR / "intents.yaml").read_text(encoding="utf-8"))
    # Sin tildes "año" y "ano" quedan iguales: deduplicar para que una frase no cuente doble.
    return [{**i, "phrases": sorted({normalize(p) for p in i["phrases"]})} for i in raw]


def classify(text: str) -> Intent:
    t = normalize(text)
    best: tuple[int, int, str] | None = None
    for item in _intents():
        hits = sum(1 for p in item["phrases"] if p in t)
        if hits:
            key = (-hits, int(item["priority"]), item["intent"])
            if best is None or key < best:
                best = key
    return best[2] if best else "help"  # type: ignore[return-value]


def extract(text: str) -> dict[str, Any]:
    t = normalize(text)
    ent: dict[str, Any] = {}
    if any(w in t for w in ("alquilo", "arriendo", "arrendatario", "arrendando")):
        ent["actor"] = "TENANT"
    elif any(w in t for w in ("propietario", "dueno", "el campo es mio")):
        ent["actor"] = "OWNER"
    elif "banco" in t:
        ent["actor"] = "BANK"
    elif "cooperativa" in t:
        ent["actor"] = "COOP"
    m = re.search(r"(\d{1,2})\s*(?:anos|ano)", t)
    if m:
        ent["years"] = int(m.group(1))
    if any(
        w in t
        for w in ("no me puedo dar el lujo", "no quiero riesgo", "poco riesgo", "conservador")
    ):
        ent["risk"] = "high_aversion"
    if "girasol" in t or "sorgo" in t or "cebada" in t:
        ent["out_of_catalog"] = True
    return ent


def _evaluate(
    state: ConversationState,
    trace: list[ToolTrace],
    year_filter: YearClassFilter = YearClassFilter.ALL,
) -> EngineOutput:
    reg = AssumptionRegistry.load()
    profile = actor_profile(reg, state.actor, horizon_years=state.horizon_override)
    inp = build_engine_input(
        profile,
        current_rotation_id=state.current_rotation_id,
        year_class_filter=year_filter,
        registry=reg,
    )
    out = evaluate(inp)
    trace.append(
        ToolTrace(
            tool="evaluate_rotations",
            params={
                "actor": state.actor,
                "current_rotation_id": state.current_rotation_id,
                "year_class_filter": year_filter.value,
                "horizon_years": state.horizon_override,
            },
            input_hash=out.input_hash,
            engine_version=out.engine_version,
        )
    )
    return out


NAMES = {r.rotation_id: r.name for r in CATALOG}


def _top(out: EngineOutput) -> Any:
    eligible = [r for r in out.results if r.eligible]
    return eligible[0] if eligible else out.results[0]


def _ranking_text(out: EngineOutput, state: ConversationState) -> str:
    lines = [
        f"Para un {ACTOR_LABEL[state.actor]}, con {len(out.years_used)} años históricos de NASA POWER:"
    ]
    for r in out.results[:3]:
        score = fmt(r.breakdown.total.value, "USD/ha") if r.breakdown else "sin puntaje"
        tag = " (tu rotación actual)" if r.is_current else ""
        elig = "" if r.eligible else " · no elegible"
        lines.append(
            f"{r.rank}. {NAMES.get(r.rotation_id, r.rotation_id)}{tag}: {score}, agua {WATER_LABEL[r.water_feasibility]}{elig}."
        )
    cur = next(r for r in out.results if r.is_current)
    if cur.rank > 3:
        lines.append(f"Tu rotación actual queda en el puesto {cur.rank}.")
    return "\n".join(lines)


def _sowing(out: EngineOutput, trace: list[ToolTrace]) -> SowingDecision:
    reg = AssumptionRegistry.load()
    d = sowing_decision(out, NAMES, reg, demo_economics(reg))
    trace.append(
        ToolTrace(
            tool="sowing_decision",
            params={
                "actor": out.profile_id,
                "rent_qq_ha": d.rent_qq,
                "alternatives": ["rent", "fallow"],
            },
            input_hash=out.input_hash,
            engine_version=out.engine_version,
        )
    )
    return d


def _sowing_text(d: SowingDecision, asks_future: bool) -> str:
    lines = [d.headline, *d.reasons]
    lines.append(
        "El arriendo de referencia (A-ECO-05) y el costo de barbecho (A-ECO-06) son supuestos de ejemplo:"
        " cambialos por los de tu contrato en la web."
    )
    if asks_future:
        lines.insert(
            0,
            "No pronostico el año que viene: te muestro qué pasó en las campañas reales del registro.",
        )
    return "\n".join(lines)


def _why_text(out: EngineOutput) -> str:
    r = _top(out)
    exp = explain(out, NAMES)
    card = next(x for x in exp.rotations if x.rotation_id == r.rotation_id)
    return "\n".join(card.sections["Por qué"])


def _risk_text(out: EngineOutput) -> str:
    r = _top(out)
    lines = [f"{NAMES.get(r.rotation_id, r.rotation_id)}:"]
    label = {"DRY": "secos", "NORMAL": "normales", "WET": "húmedos"}
    for m in r.margin_ranges:
        lines.append(
            f"En años {label[m.year_class.value]} el margen anual fue de {fmt(m.minimum.value, 'USD/ha')} a {fmt(m.maximum.value, 'USD/ha')}."
        )
    if r.loss_years is not None:
        lines.append(
            f"Habrías perdido plata en {r.loss_years.count} de {r.loss_years.total} años reales."
        )
    lines.append(
        "No damos un porcentaje de confianza: mostramos cómo le fue en los años reales. Los supuestos económicos son de ejemplo y están pendientes de validar con AFA."
    )
    return "\n".join(lines)


def _water_text(out: EngineOutput) -> str:
    lines = []
    for r in out.results:
        reasons = ", ".join(
            x
            for x in r.water_reasons
            if x
            in (
                "SEVERE_STRESS_FREQUENT",
                "PROFILE_NOT_RECHARGED_AT_SOWING",
                "INITIAL_MOISTURE_ASSUMED",
            )
        )
        lines.append(
            f"{NAMES.get(r.rotation_id, r.rotation_id)}: agua {WATER_LABEL[r.water_feasibility]}{f' ({reasons})' if reasons else ''}."
        )
    lines.append("La humedad inicial todavía es un supuesto: falta cargar SMAP L4 del lote.")
    return "\n".join(lines)


def _bare_text(out: EngineOutput) -> str:
    months = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
    lines = []
    for r in out.results:
        if r.bare_soil_calendar is None:
            continue
        bare = [months[i] for i, d in enumerate(r.bare_soil_calendar.days_by_month) if d >= 15]
        rain = (
            f", con {fmt(r.rain_on_bare_soil.value, 'mm')} de lluvia por año sobre suelo desnudo"
            if r.rain_on_bare_soil
            else ""
        )
        lines.append(
            f"{NAMES.get(r.rotation_id, r.rotation_id)}: desnudo en {', '.join(bare) if bare else 'ningún mes'}{rain}."
        )
    return "\n".join(lines)


def _vulnerability_text(out: EngineOutput) -> str:
    exp = explain(out, NAMES)
    r = _top(out)
    card = next(x for x in exp.rotations if x.rotation_id == r.rotation_id)
    vul = card.extras.get("Meses vulnerables", ["No hay meses con eventos frecuentes."])
    return f"{NAMES.get(r.rotation_id, r.rotation_id)}:\n" + "\n".join(vul)


def _glossary_text(text: str) -> str:
    t = normalize(text)
    for g in load_glossary():
        keys = [normalize(g["term"]), g["id"].replace("_", " ")]
        if any(k.split(" (")[0] in t for k in keys):
            return f"{g['term']}: {g['short']}"
    return "Puedo explicarte: " + ", ".join(g["term"] for g in load_glossary()) + "."


def respond(req: AskRequest) -> AskResponse:
    intent = classify(req.text)
    ent = extract(req.text)
    state = req.state
    trace: list[ToolTrace] = []
    compare = False
    if ent.get("out_of_catalog"):
        text = "Ese cultivo no está en el catálogo del MVP (soja, maíz, trigo y servicios de vicia, centeno o avena). Puedo comparar las rotaciones disponibles."
        return AskResponse(
            text=text, intent=intent, trace=trace, state=state, suggestions=list(SUGGESTIONS[:2])
        )
    if state.pending_profile and normalize(req.text) in ("si", "sí", "dale", "ok", "correcto"):
        state = state.model_copy(update={"actor": state.pending_profile, "pending_profile": None})
        intent = "ranking"
    if intent == "sowing":
        actor = ent.get("actor", state.actor)
        state = state.model_copy(update={"actor": actor, "pending_profile": None})
        out = _evaluate(state, trace)
        t = normalize(req.text)
        text = _sowing_text(
            _sowing(out, trace),
            any(w in t for w in ("ano que viene", "proximo ano", "proxima campana")),
        )
    elif intent == "scope":
        text = "No pronostico el clima ni precios. Trabajo con años históricos reales: puedo mostrarte cómo le fue a cada rotación en los años secos del registro."
    elif intent == "describe_situation":
        actor = ent.get("actor", state.actor)
        years = ent.get("years")
        if ent.get("risk") == "high_aversion" and actor == "OWNER":
            actor = "BANK"
        trace.append(
            ToolTrace(
                tool="propose_profile",
                params={"actor": actor, "years": years, "risk": ent.get("risk")},
            )
        )
        horizon = f", con un horizonte de {years} años" if years else ""
        text = f"Entiendo que decidís como {ACTOR_LABEL[actor]}{horizon}. ¿Es correcto? Respondé sí para ver el ranking con ese perfil."
        state = state.model_copy(
            update={
                "pending_profile": actor,
                "horizon_override": years if years and 1 <= years <= 20 else None,
            }
        )
    elif intent == "help":
        text = "Puedo contestarte qué rotación conviene, por qué, qué pasa en años secos, cuánto riesgo hay, cuándo queda el suelo desnudo y qué significan los términos."
    elif intent == "glossary":
        trace.append(ToolTrace(tool="glossary", params={"query": req.text[:60]}))
        text = _glossary_text(req.text)
    elif intent == "assumptions":
        trace.append(ToolTrace(tool="list_assumptions", params={}))
        text = "Los precios, costos, rindes y perfiles de actor son supuestos de ejemplo, registrados con su id (A-DEMO-02 a A-DEMO-06, A-ACT-01 a A-ACT-04) y pendientes de validar con AFA. Los datos de clima vienen de NASA POWER."
    elif intent == "compare_actors":
        compare = True
        a = _evaluate(state.model_copy(update={"actor": "OWNER"}), trace)
        b = _evaluate(state.model_copy(update={"actor": "TENANT"}), trace)
        text = (
            f"Como propietario gana {NAMES[_top(a).rotation_id]}; como arrendatario, {NAMES.get(_top(b).rotation_id, _top(b).rotation_id)}. "
            "El dueño mira más años y valora el suelo; el arrendatario mira la campaña y tiene menos capital."
        )
    else:
        flt = YearClassFilter.DRY if intent == "what_if_dry" else YearClassFilter.ALL
        out = _evaluate(state, trace, flt)
        if intent in ("ranking", "what_if_dry"):
            # "¿Me conviene?" a secas: primero el sí o no, después el orden.
            head = _sowing(out, trace).headline + "\n\n" if intent == "ranking" else ""
            text = (
                head
                + (
                    "Mirando solo los años secos del registro.\n"
                    if flt is YearClassFilter.DRY
                    else ""
                )
                + _ranking_text(out, state)
            )
        elif intent == "why":
            text = _why_text(out)
        elif intent == "risk":
            text = _risk_text(out)
        elif intent == "water":
            text = _water_text(out)
        elif intent == "bare_soil":
            text = _bare_text(out)
        else:
            text = _vulnerability_text(out)
    if intent in ("sowing", "ranking", "what_if_dry", "why", "risk") or compare:
        text = f"{text}\n\n{DISCLAIMERS[0]} {DISCLAIMERS[1]}"
    suggestions = [s for s in SUGGESTIONS if normalize(s) != normalize(req.text)][:3]
    return AskResponse(text=text, intent=intent, trace=trace, state=state, suggestions=suggestions)


__all__ = [
    "AskRequest",
    "AskResponse",
    "ConversationState",
    "classify",
    "extract",
    "respond",
    "PROFILE_ASSUMPTIONS",
    "CATALOG_BY_ID",
]
