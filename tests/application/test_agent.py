from __future__ import annotations

import pytest

from rastrojo.application.agent import AskRequest, ConversationState, classify, extract, respond
from rastrojo.application.explanations import forbidden_hits, load_forbidden
from rastrojo.domain import canonical_json


@pytest.mark.parametrize(
    "text,intent",
    [
        ("¿Cuál me conviene?", "ranking"),
        ("¿qué me rinde más?", "ranking"),
        ("¿Por qué sale primera?", "why"),
        ("¿Y si el año viene seco?", "what_if_dry"),
        ("¿Qué tan seguro es esto?", "risk"),
        ("¿va a llover el año que viene?", "scope"),
        ("alquilo por dos años y no me puedo dar el lujo de un mal año", "describe_situation"),
        ("¿qué es el NDVI?", "glossary"),
        ("¿cuándo queda el suelo desnudo?", "bare_soil"),
        ("¿cómo está el clima en Marte?", "help"),
    ],
)
def test_classify(text: str, intent: str) -> None:
    assert classify(text) == intent


def test_extract_tenant_two_years() -> None:
    e = extract("alquilo por 2 años y no me puedo dar el lujo")
    assert e["actor"] == "TENANT" and e["years"] == 2 and e["risk"] == "high_aversion"


def test_ranking_has_trace_and_disclaimers() -> None:
    r = respond(AskRequest(text="¿Cuál me conviene?"))
    assert r.trace and r.trace[0].tool == "evaluate_rotations" and r.trace[0].input_hash
    assert "apoya, no reemplaza" in r.text and r.mode == "scripted"


def test_trace_reproduces_evaluate() -> None:
    from fastapi.testclient import TestClient

    from rastrojo.adapters.api import create_app

    r = respond(AskRequest(text="¿Cuál me conviene?"))
    c = TestClient(create_app())
    body = c.post(
        "/api/v1/evaluate", json={"actor": "OWNER", "current_rotation_id": "R_SOY_MONO"}
    ).json()
    assert body["input_hash"] == r.trace[0].input_hash


def test_profile_proposal_then_confirm() -> None:
    r1 = respond(AskRequest(text="alquilo por 2 años, soy arrendatario"))
    assert r1.state.pending_profile == "TENANT" and "¿Es correcto?" in r1.text
    r2 = respond(AskRequest(text="sí", state=r1.state))
    assert r2.state.actor == "TENANT" and r2.intent == "ranking"


def test_scope_no_forecast() -> None:
    r = respond(AskRequest(text="¿va a llover el año que viene?"))
    assert "No pronostico" in r.text and not r.trace


def test_out_of_catalog() -> None:
    assert "catálogo" in respond(AskRequest(text="yo hago girasol, ¿me conviene?")).text


def test_no_forbidden_and_deterministic() -> None:
    phrases = load_forbidden()
    for t in (
        "¿Cuál me conviene?",
        "¿Por qué sale primera?",
        "¿Qué tan seguro es esto?",
        "¿Y si el año viene seco?",
    ):
        a = respond(AskRequest(text=t, state=ConversationState(actor="BANK")))
        b = respond(AskRequest(text=t, state=ConversationState(actor="BANK")))
        assert canonical_json(a) == canonical_json(b)
        assert forbidden_hits(a.text, phrases) == []
