from __future__ import annotations

from fastapi.testclient import TestClient

from rastrojo.adapters.api import create_app

client = TestClient(create_app())
P = "/api/v1"


def test_health() -> None:
    r = client.get(f"{P}/health")
    assert r.status_code == 200 and r.json()["engine_version"]


def test_catalog_and_profiles() -> None:
    assert len(client.get(f"{P}/rotations/catalog").json()["rotations"]) == 5
    body = client.get(f"{P}/actors/profiles").json()
    assert {p["profile_id"] for p in body["profiles"]} == {"OWNER", "TENANT", "COOP", "BANK"}
    assert "alpha" in body["slider_limits"]


def test_evaluate_lite_idempotent_with_hash_header() -> None:
    a = client.post(f"{P}/evaluate", json={"actor": "OWNER"})
    b = client.post(f"{P}/evaluate", json={"actor": "OWNER"})
    assert a.status_code == 200
    assert a.content == b.content
    assert a.headers["X-Input-Hash"] == a.json()["input_hash"]
    assert len(a.json()["engine_output"]["results"]) == 5


def test_actor_changes_ranking() -> None:
    owner = [
        r["rotation_id"]
        for r in client.post(f"{P}/evaluate", json={"actor": "OWNER"}).json()["engine_output"][
            "results"
        ]
    ]
    bank = [
        r["rotation_id"]
        for r in client.post(f"{P}/evaluate", json={"actor": "BANK"}).json()["engine_output"][
            "results"
        ]
    ]
    assert owner != bank


def test_slider_override_changes_hash() -> None:
    a = client.post(f"{P}/evaluate", json={"actor": "OWNER"}).json()["input_hash"]
    b = client.post(
        f"{P}/evaluate", json={"actor": "OWNER", "overrides": {"risk_aversion": 2.0}}
    ).json()["input_hash"]
    assert a != b


def test_display_preferences_do_not_change_hash() -> None:
    a = client.post(f"{P}/evaluate", json={"actor": "OWNER"}).json()
    b = client.post(
        f"{P}/evaluate", json={"actor": "OWNER", "display_preferences": ["WATER_SAFE_FIRST"]}
    ).json()
    assert a["input_hash"] == b["input_hash"]
    assert b["display_order"][0] == "R_SOY_MONO"  # la única FEASIBLE en agua del demo


def test_typed_errors() -> None:
    r = client.post(f"{P}/evaluate", json={"actor": "ALIEN"})
    assert r.status_code == 422 and r.json()["code"] == "UNKNOWN_ACTOR"
    r = client.post(f"{P}/evaluate", json={"current_rotation_id": "R_GIRASOL"})
    assert r.json()["code"] == "UNKNOWN_ROTATION"
    r = client.post(f"{P}/evaluate", json={"color": "rojo"})
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"
    r = client.post(f"{P}/evaluate", json={"plot_id": "otro-lote"})
    assert r.status_code == 404 and r.json()["code"] == "PLOT_NOT_FOUND"
    r = client.get(f"{P}/nada")
    assert r.json()["code"] == "NOT_FOUND"
    r = client.post(f"{P}/evaluate", content="x", headers={"content-type": "text/plain"})
    assert r.status_code == 415


def test_slider_out_of_limits() -> None:
    r = client.post(f"{P}/evaluate", json={"overrides": {"alpha": 50}})
    assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"


def test_cors_header() -> None:
    r = client.options(
        f"{P}/evaluate",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_evaluate_includes_explanation_and_glossary() -> None:
    body = client.post(f"{P}/evaluate", json={"actor": "OWNER"}).json()
    assert body["explanation"]["disclaimers"] and "Por qué" in body["explanation_text"]
    terms = client.get(f"{P}/glossary").json()["terms"]
    assert any(t["id"] == "satellite_vs_field" for t in terms)
