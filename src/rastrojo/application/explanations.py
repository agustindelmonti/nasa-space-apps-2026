"""Explicaciones deterministas por plantillas a partir de la salida del motor (sin LLM).

Cada número del texto sale de la salida del motor y se formatea con `format_ar`, así un test
puede extraer los números del texto y encontrarlos en la salida.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

from rastrojo.domain.crops import CROP_INFO, Crop
from rastrojo.domain.engine_io import EngineOutput
from rastrojo.domain.results import RotationResult, WaterFeasibility

TEMPLATES_VERSION = "0.1.0"
DISCLAIMERS = (
    "Esta herramienta apoya, no reemplaza, al agrónomo.",
    "Son escenarios con años históricos, no una predicción.",
)
DATA_DIR = Path(__file__).resolve().parents[3] / "data"

DECIMALS = {
    "USD/ha": 0,
    "USD/t": 0,
    "mm": 0,
    "mm/day": 1,
    "index": 1,
    "m3/m3": 2,
    "degC": 1,
    "t/ha": 1,
    "count": 0,
    "days": 0,
    "fraction": 2,
    "ratio": 2,
    "%": 1,
    "ha": 0,
}
UNIT_LABEL = {
    "USD/ha": "USD/ha",
    "mm": "mm",
    "mm/day": "mm/día",
    "index": "puntos",
    "m3/m3": "m³/m³",
    "degC": "°C",
    "t/ha": "t/ha",
    "ha": "ha",
}
WATER_LABEL = {
    WaterFeasibility.FEASIBLE: "factible",
    WaterFeasibility.RISKY: "riesgosa",
    WaterFeasibility.NOT_FEASIBLE: "no factible",
    WaterFeasibility.UNKNOWN: "desconocida",
}
REASON_LABEL = {
    "DOUBLE_CROP_NOT_ALLOWED": "el actor no hace doble cultivo",
    "COVER_NOT_ALLOWED": "el actor no hace cultivos de servicio",
    "WORKING_CAPITAL_EXCEEDED": "supera el capital de trabajo disponible",
    "WATER_NEVER_FEASIBLE": "en el registro histórico nunca hubo agua para sembrarla",
    "MACHINERY_WINDOW_CONFLICT": "no entra en las ventanas de maquinaria",
    "MISSING_PARAMETERS": "faltan datos para calcularla",
}
MONTHS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
CARD_SECTIONS = ("Por qué", "Evidencia", "Beneficios", "Qué falta saber", "Riesgos")


# ---------------------------------------------------------------------------
# Formato numérico argentino
# ---------------------------------------------------------------------------


def format_ar(value: float, unit: str | None = None, signed: bool = False) -> str:
    digits = DECIMALS.get(unit or "", 1)
    q = Decimal(repr(float(value))).quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    neg = q < 0
    q = abs(q)
    text = f"{q:.{digits}f}"
    int_part, _, dec = text.partition(".")
    groups: list[str] = []
    while len(int_part) > 3:
        groups.insert(0, int_part[-3:])
        int_part = int_part[:-3]
    groups.insert(0, int_part)
    out = ".".join(groups) + ("," + dec if dec else "")
    if neg and q != 0:
        out = "-" + out
    elif signed and q != 0:
        out = "+" + out
    return out


def fmt(value: float, unit: str, signed: bool = False) -> str:
    label = UNIT_LABEL.get(unit)
    num = format_ar(value, unit, signed)
    return f"{num} {label}" if label else num


_NUM_RE = re.compile(
    r"(?<![\w-])[-+]?\d{1,3}(?:\.\d{3})*(?:,\d+)?(?![\w])|(?<![\w-])[-+]?\d+(?:,\d+)?(?![\w])"
)


def parse_ar_numbers(text: str) -> list[float]:
    """Números en formato argentino. Ignora ids de supuestos (A-XXX-NN) y marcadores (n/m)."""
    cleaned = re.sub(r"A-[A-Z]+-\d{2}|FAO-56|GRACE-FO|SMAP L4|IMERG|MOD13Q1", " ", text)
    cleaned = re.sub(r"\(\d+/\d+\)", " ", cleaned)
    out: list[float] = []
    for m in _NUM_RE.finditer(cleaned):
        raw = m.group(0)
        out.append(float(raw.replace(".", "").replace(",", ".")))
    return out


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RotationExplanation(_Frozen):
    rotation_id: str
    title: str
    sections: dict[str, list[str]]
    extras: dict[str, list[str]]
    closing: str


class Explanation(_Frozen):
    input_hash: str
    engine_version: str
    templates_version: str
    summary: list[str]
    rotations: list[RotationExplanation]
    disclaimers: list[str]
    assumption_ids: list[str]


# ---------------------------------------------------------------------------
# Plantillas
# ---------------------------------------------------------------------------


def _crop(c: Crop | str) -> str:
    return CROP_INFO[Crop(c)].label_es.lower()


def _dominant(r: RotationResult) -> str:
    b = r.breakdown
    assert b is not None
    terms = {
        "el margen esperado": abs(b.npv.value),
        "el aporte al suelo": abs(b.soil_term.value),
        "la penalidad por riesgo": abs(b.risk_term.value),
    }
    return max(terms, key=lambda k: terms[k])


def _why(r: RotationResult, names: dict[str, str], current: RotationResult) -> list[str]:
    lines: list[str] = []
    name = names.get(r.rotation_id, r.rotation_id)
    if not r.eligible:
        motivos = ", ".join(REASON_LABEL.get(x.value, x.value) for x in r.exclusion_reasons)
        lines.append(f"{name} queda fuera de las opciones elegibles porque {motivos}.")
    else:
        lines.append(
            f"{name} queda en el puesto {r.rank} con {fmt(r.breakdown.total.value, 'USD/ha')} de puntaje."
            if r.breakdown
            else f"{name} no tiene puntaje."
        )
    if r.breakdown is not None:
        b = r.breakdown
        lines.append(
            f"El puntaje suma el margen descontado ({fmt(b.npv.value, 'USD/ha')}), el aporte al suelo ({fmt(b.soil_term.value, 'USD/ha', True)}) "
            f"y resta la penalidad por riesgo ({fmt(b.risk_term.value, 'USD/ha')}). Lo que más pesa es {_dominant(r)}."
        )
    if not r.is_current and r.score_delta_vs_current is not None:
        d = r.score_delta_vs_current.value
        cur = names.get(current.rotation_id, current.rotation_id)
        rel = "más" if d > 0 else "menos"
        lines.append(
            f"Frente a la rotación actual ({cur}) suma {fmt(abs(d), 'USD/ha')} {rel} de puntaje."
        )
    elif r.is_current:
        lines.append("Es la rotación que hacés hoy.")
    agua = WATER_LABEL[r.water_feasibility]
    if r.water_feasibility is WaterFeasibility.UNKNOWN:
        lines.append(
            "La factibilidad hídrica es desconocida: faltan datos de clima para decidirla (ver qué falta saber)."
        )
    else:
        lines.append(f"En agua, con el clima de los años históricos, es {agua}.")
    return lines


def _evidence(r: RotationResult) -> list[str]:
    out = []
    for e in r.evidence:
        out.append(
            f"{e.dataset.value} · {e.variable}: {fmt(e.value.value, e.value.unit)} ({e.period.start.year} a {e.period.end.year}). {e.interpretation}"
        )
    return out or ["Sin evidencia satelital adicional para esta rotación."]


def _benefits(r: RotationResult) -> list[str]:
    out = [
        f"{b.description}: {fmt(b.value.value, b.value.unit, True)}."
        if b.value
        else f"{b.description}."
        for b in r.benefits
    ]
    return out or ["No suma puntos de suelo frente a la referencia."]


def _missing(r: RotationResult) -> list[str]:
    seen: list[str] = []
    for m in r.missing:
        line = (
            f"{m.item[0].upper()}{m.item[1:]}: {m.why_it_matters} Cómo conseguirlo: {m.how_to_get}"
        )
        if line not in seen:
            seen.append(line)
    return seen or ["No hay faltantes registrados para esta rotación."]


SEVERITY = {"LOW": "baja", "MEDIUM": "media", "HIGH": "alta"}


def _risks(r: RotationResult) -> list[str]:
    out = []
    if r.risk is not None and r.breakdown is not None:
        out.append(
            f"Riesgo económico: en el peor tercio de los años el margen cae en promedio {fmt(r.risk.value, 'USD/ha')} "
            "por debajo del esperado (acumulado en el horizonte del actor)."
        )
    for k in r.risks:
        base = "dato" if k.basis == "EVIDENCE" else f"supuesto {k.reference}"
        out.append(f"{k.description} Severidad {SEVERITY[k.severity.value]} (según {base}).")
    return out or ["Sin riesgos registrados más allá de la variabilidad del clima."]


def _extras(r: RotationResult) -> dict[str, list[str]]:
    ex: dict[str, list[str]] = {}
    if r.margin_ranges:
        label = {"DRY": "secos", "NORMAL": "normales", "WET": "húmedos"}
        ex["Incertidumbre"] = [
            f"En años {label[m.year_class.value]} el margen anual va de {fmt(m.minimum.value, 'USD/ha')} a {fmt(m.maximum.value, 'USD/ha')} (esperado {fmt(m.expected.value, 'USD/ha')})."
            for m in r.margin_ranges
        ]
    if r.loss_years is not None and r.worst_year_margin is not None and r.worst_year is not None:
        ly = r.loss_years
        line = f"Habrías perdido plata en {ly.count} de {ly.total} años reales"
        line += f" ({', '.join(str(y) for y in ly.years)})." if ly.years else "."
        ex["Años malos"] = [
            line,
            f"Margen en el peor año ({r.worst_year}): {fmt(r.worst_year_margin.value, 'USD/ha')}.",
        ]
    if r.bare_soil_calendar is not None:
        bare = [MONTHS[i] for i, d in enumerate(r.bare_soil_calendar.days_by_month) if d >= 15]
        lines = [
            f"Suelo desnudo la mayor parte del mes en: {', '.join(bare)}."
            if bare
            else "El suelo queda cubierto casi todo el año."
        ]
        if r.rain_on_bare_soil is not None:
            lines.append(
                f"Lluvia que cae sobre suelo desnudo: {fmt(r.rain_on_bare_soil.value, 'mm')} por año en promedio."
            )
        ex["Suelo desnudo"] = lines
    vul: list[str] = []
    ev_label = {
        "FROST": "helada",
        "WATER_DEFICIT": "déficit de agua",
        "HEAT_STRESS": "calor en floración",
        "EXTREME_RAIN": "lluvia extrema",
    }
    for v in r.vulnerability_calendar:
        months = [
            MONTHS[i]
            for i, lv in enumerate(v.level_by_month)
            if lv is not None and lv.value != "LOW"
        ]
        if months:
            vul.append(
                f"{_crop(v.crop).capitalize()}: {ev_label[v.event]} frecuente en {', '.join(months)}."
            )
    if vul:
        ex["Meses vulnerables"] = vul
    return ex


def explain(output: EngineOutput, names: dict[str, str]) -> Explanation:
    current = next(r for r in output.results if r.is_current)
    rotations = [
        RotationExplanation(
            rotation_id=r.rotation_id,
            title=f"{r.rank}. {names.get(r.rotation_id, r.rotation_id)}{' (actual)' if r.is_current else ''}",
            sections={
                CARD_SECTIONS[0]: _why(r, names, current),
                CARD_SECTIONS[1]: _evidence(r),
                CARD_SECTIONS[2]: _benefits(r),
                CARD_SECTIONS[3]: _missing(r),
                CARD_SECTIONS[4]: _risks(r),
            },
            extras=_extras(r),
            closing=DISCLAIMERS[0],
        )
        for r in output.results
    ]
    top = [r for r in output.results if r.eligible][:3]
    summary = [
        f"Comparamos {len(output.results)} rotaciones para el perfil {output.profile_id} con {len(output.years_used)} años históricos de NASA POWER."
    ]
    if top:
        summary.append(
            "Primeras elegibles: "
            + "; ".join(
                f"{r.rank}. {names.get(r.rotation_id, r.rotation_id)} ({WATER_LABEL[r.water_feasibility]} en agua)"
                for r in top
            )
            + "."
        )
    summary.append(
        f"Tu rotación actual ({names.get(current.rotation_id, current.rotation_id)}) queda en el puesto {current.rank}."
    )
    if "LOW_ELIGIBLE_COUNT" in output.warnings:
        summary.append(
            "Con las restricciones de este actor quedan menos de tres opciones elegibles; mostramos igual las descartadas con su motivo."
        )
    ids = sorted(
        {
            w
            for r in output.results
            for k in r.risks
            if k.basis == "ASSUMPTION"
            for w in [k.reference]
        }
    )
    return Explanation(
        input_hash=output.input_hash,
        engine_version=output.engine_version,
        templates_version=TEMPLATES_VERSION,
        summary=summary,
        rotations=rotations,
        disclaimers=list(DISCLAIMERS),
        assumption_ids=ids,
    )


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_web(exp: Explanation) -> str:
    parts = ["\n".join(exp.summary)]
    for r in exp.rotations:
        block = [f"## {r.title}"]
        for sec, lines in r.sections.items():
            block.append(f"**{sec}**")
            block += [f"- {x}" for x in lines]
        for sec, lines in r.extras.items():
            block.append(f"**{sec}**")
            block += [f"- {x}" for x in lines]
        block.append(r.closing)
        parts.append("\n".join(block))
    parts.append("\n".join(exp.disclaimers))
    return "\n\n".join(parts)


def render_whatsapp(exp: Explanation, top_n: int = 3) -> str:
    lines = list(exp.summary)
    for r in exp.rotations[:top_n]:
        why = r.sections[CARD_SECTIONS[0]]
        lines.append(f"*{r.title}*\n" + " ".join(why[:2]))
    lines.append("Escribí *detalle* para ver la evidencia o *glosario* para los términos.")
    return "\n\n".join(lines)


def partition(text: str, limit: int = 1600, tail: tuple[str, ...] = DISCLAIMERS) -> list[str]:
    """Partición determinista por párrafo, línea y palabra; las leyendas van en el último mensaje."""
    tail_text = "\n".join(tail)
    units: list[str] = []
    for para in text.split("\n\n"):
        units.append(para)

    def split_unit(u: str, room: int) -> list[str]:
        if len(u) <= room:
            return [u]
        pieces: list[str] = []
        current = ""
        for word in u.replace("\n", " \n ").split(" "):
            cand = f"{current} {word}".strip(" ") if current else word
            if len(cand) > room and current:
                pieces.append(current.strip())
                current = word
            else:
                current = cand
        if current.strip():
            pieces.append(current.strip())
        return pieces

    marker_room = 8
    for m_guess in range(1, 50):
        room = limit - marker_room
        msgs: list[str] = []
        cur = ""
        flat: list[str] = []
        for u in units:
            flat += split_unit(u, room)
        for u in flat:
            cand = f"{cur}\n\n{u}" if cur else u
            if len(cand) > room:
                msgs.append(cur)
                cur = u
            else:
                cur = cand
        last = f"{cur}\n\n{tail_text}" if cur else tail_text
        if len(last) > room:
            msgs.append(cur)
            last = tail_text
        msgs.append(last)
        if len(msgs) == m_guess or m_guess >= len(msgs):
            break
    if len(msgs) == 1:
        return msgs
    n = len(msgs)
    return [f"{m}\n({i}/{n})" for i, m in enumerate(msgs, start=1)]


# ---------------------------------------------------------------------------
# Glosario y frases prohibidas
# ---------------------------------------------------------------------------


def load_glossary(path: Path | None = None) -> list[dict[str, Any]]:
    return list(yaml.safe_load((path or DATA_DIR / "glossary.yaml").read_text(encoding="utf-8")))


def load_forbidden(path: Path | None = None) -> list[str]:
    return [
        str(x).lower()
        for x in yaml.safe_load(
            (path or DATA_DIR / "forbidden_phrases.yaml").read_text(encoding="utf-8")
        )
    ]


def forbidden_hits(text: str, phrases: list[str]) -> list[str]:
    low = text.lower()
    return [p for p in phrases if p in low]
