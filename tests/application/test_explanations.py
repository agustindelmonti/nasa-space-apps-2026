from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from rastrojo.application.demo import CATALOG
from rastrojo.application.explanations import (
    CARD_SECTIONS,
    DISCLAIMERS,
    explain,
    forbidden_hits,
    format_ar,
    load_forbidden,
    load_glossary,
    parse_ar_numbers,
    partition,
    render_web,
    render_whatsapp,
)
from rastrojo.domain import canonical_json
from rastrojo.engine.rotation import evaluate
from tests.engine.engine_fixtures import demo_input, profile

NAMES = {r.rotation_id: r.name for r in CATALOG}


def _out(pid="OWNER"):
    return evaluate(demo_input(profile(pid)))


def test_format_ar_examples() -> None:
    assert format_ar(1234.5, "USD/ha") == "1.235"
    assert format_ar(0.675, "m3/m3") == "0,68"
    assert format_ar(-12.34, "index") == "-12,3"


@given(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False))
def test_parse_round_trip(v) -> None:
    text = f"valor {format_ar(v, 'index')} puntos"
    parsed = parse_ar_numbers(text)
    assert parsed and parsed[0] == pytest.approx(
        float(format_ar(v, "index").replace(".", "").replace(",", "."))
    )


def test_card_has_five_sections_and_closing() -> None:
    exp = explain(_out(), NAMES)
    for r in exp.rotations:
        assert tuple(r.sections) == CARD_SECTIONS
        assert r.closing == DISCLAIMERS[0]
    assert exp.disclaimers == list(DISCLAIMERS)


def _all_numbers_in_output(out) -> set[str]:
    """Todos los valores numéricos de la salida formateados como los formatea el texto."""
    import json

    data = json.loads(canonical_json(out))
    found: set[str] = set()

    def walk(x, unit=None):
        if isinstance(x, dict):
            u = x.get("unit", unit)
            for _k, v in x.items():
                walk(v, u)
        elif isinstance(x, list):
            for v in x:
                walk(v, unit)
        elif isinstance(x, str):
            m = __import__("re").match(r"^(\d{4})-\d{2}-\d{2}$", x)
            if m:
                found.add(m.group(1))
        elif isinstance(x, bool):
            return
        elif isinstance(x, int | float):
            for un in (unit, "USD/ha", "index", "mm", "count"):
                found.add(format_ar(abs(x), un))
            found.add(str(int(x)) if float(x).is_integer() else "")

    walk(data)
    return found


def test_every_number_in_text_is_traceable() -> None:
    out = _out()
    exp = explain(out, NAMES)
    text = render_web(exp)
    allowed = _all_numbers_in_output(out) | {
        format_ar(len(out.results), "count"),
        format_ar(len(out.years_used), "count"),
    }
    allowed |= {str(i) for i in range(0, 13)}  # puestos y conteos chicos
    allowed |= {
        "9",
        "250",
        "300",
        "2",
        "30",
        "50",
    }  # resoluciones y alturas del catálogo de datasets (9 km, 250 m, 300 km, 2 m, 30 m, 50 km)
    import re

    clean = re.sub(r"A-[A-Z]+-\d{2}|FAO-56|SMAP L4", " ", text)
    for raw in re.findall(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?(?!\d)|\d+(?:,\d+)?", clean):
        assert raw.lstrip("+-") in allowed, f"número no trazable: {raw}"


def test_no_forbidden_phrases_in_all_actors() -> None:
    phrases = load_forbidden()
    for pid in ("OWNER", "TENANT", "COOP", "BANK"):
        exp = explain(_out(pid), NAMES)
        assert forbidden_hits(render_web(exp), phrases) == []
        assert forbidden_hits(render_whatsapp(exp), phrases) == []


def test_forbidden_detector_catches() -> None:
    assert forbidden_hits("El modelo predice lluvia con 85 % de confianza", load_forbidden())


def test_partition_single_and_long() -> None:
    short = "a" * 500
    assert partition(short) == [short + "\n\n" + "\n".join(DISCLAIMERS)]
    long = "\n\n".join(["palabra " * 60] * 12)
    msgs = partition(long)
    assert len(msgs) > 1 and all(len(m) <= 1600 for m in msgs)
    assert msgs[-1].count(DISCLAIMERS[0]) == 1 and msgs[-1].endswith(f"({len(msgs)}/{len(msgs)})")
    assert partition(long) == msgs


def test_whatsapp_render_partitions_with_disclaimers() -> None:
    msgs = partition(render_whatsapp(explain(_out(), NAMES)))
    assert DISCLAIMERS[1] in msgs[-1]


def test_glossary_complete() -> None:
    ids = {g["id"] for g in load_glossary()}
    assert {
        "evapotranspiration",
        "ndvi",
        "soil_moisture_anomaly",
        "water_balance",
        "frost",
        "heat_stress",
        "grace_fo",
        "satellite_vs_field",
    } <= ids
    sat = next(g for g in load_glossary() if g["id"] == "satellite_vs_field")
    assert "Combinarlos mejora la precisión" in sat["long"]


def test_deterministic_text() -> None:
    a = render_web(explain(_out(), NAMES))
    b = render_web(explain(_out(), NAMES))
    assert a == b
