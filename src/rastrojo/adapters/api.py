"""API HTTP de Rastrojo (FastAPI). El motor no sabe nada del canal: esto solo adapta."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from rastrojo import __version__
from rastrojo.application.agent import AskRequest, respond
from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import (
    CATALOG,
    CATALOG_BY_ID,
    DEMO_PLOT_ID,
    PROFILE_ASSUMPTIONS,
    actor_profile,
    build_engine_input,
    demo_economics,
)
from rastrojo.application.explanations import explain, load_glossary, render_web
from rastrojo.application.sowing import sowing_decision
from rastrojo.data.errors import DataError
from rastrojo.domain import Rotation, YearClassFilter, canonical_json
from rastrojo.domain.actor import MachineryWindows, SoilPriorities
from rastrojo.domain.results import WaterFeasibility
from rastrojo.engine.rotation import ENGINE_VERSION, evaluate

API_PREFIX = "/api/v1"


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    engine_timeout_s: float = 20.0
    max_body_bytes: int = 64_000
    demo_mode: bool = False


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    UNKNOWN_ROTATION = "UNKNOWN_ROTATION"
    UNKNOWN_ACTOR = "UNKNOWN_ACTOR"
    OUT_OF_COVERAGE = "OUT_OF_COVERAGE"
    PLOT_NOT_FOUND = "PLOT_NOT_FOUND"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    RATE_LIMITED = "RATE_LIMITED"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    ENGINE_ERROR = "ENGINE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


_STATUS = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.MISSING_PARAMETER: 422,
    ErrorCode.UNKNOWN_ROTATION: 422,
    ErrorCode.UNKNOWN_ACTOR: 422,
    ErrorCode.OUT_OF_COVERAGE: 422,
    ErrorCode.PLOT_NOT_FOUND: 404,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.METHOD_NOT_ALLOWED: 405,
    ErrorCode.UNSUPPORTED_MEDIA_TYPE: 415,
    ErrorCode.PAYLOAD_TOO_LARGE: 413,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.DATA_UNAVAILABLE: 503,
    ErrorCode.TIMEOUT: 504,
    ErrorCode.ENGINE_ERROR: 500,
    ErrorCode.INTERNAL_ERROR: 500,
}


class ApiError(Exception):
    def __init__(self, code: ErrorCode, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def canonical_response(
    payload: Any, status: int = 200, headers: dict[str, str] | None = None
) -> Response:
    body = canonical_json(payload) if not isinstance(payload, bytes) else payload
    return Response(
        content=body, status_code=status, media_type="application/json", headers=headers
    )


def error_response(code: ErrorCode, message: str, details: Any = None) -> Response:
    return canonical_response(
        {"code": code.value, "message": message, "details": details}, _STATUS[code]
    )


# ---------------------------------------------------------------------------
# Contratos
# ---------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProfileOverrides(_Strict):
    horizon_years: int | None = Field(default=None, ge=1, le=20)
    alpha: float | None = Field(default=None, ge=0)
    risk_aversion: float | None = Field(default=None, ge=0)
    discount_rate: float | None = Field(default=None, ge=0, le=1)
    priorities: SoilPriorities | None = None
    machinery_windows: MachineryWindows | None = None


DisplayPreference = Literal["WATER_SAFE_FIRST", "DOUBLE_CROP_FIRST"]


class LiteEvaluateRequest(_Strict):
    mode: Literal["lite"] = "lite"
    plot_id: str = DEMO_PLOT_ID
    current_rotation_id: str | None = "R_SOY_MONO"
    current_rotation: Rotation | None = None
    actor: str = "OWNER"
    overrides: ProfileOverrides | None = None
    year_class_filter: YearClassFilter = YearClassFilter.ALL
    display_preferences: tuple[DisplayPreference, ...] = ()
    # Alternativas sin cultivo para "¿me conviene sembrar?": si faltan se usan A-ECO-05 y A-ECO-06.
    rent_qq_ha: float | None = Field(default=None, ge=0, le=60)
    fallow_cost_usd_ha: float | None = Field(default=None, ge=0, le=500)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


def _registry() -> AssumptionRegistry:
    return AssumptionRegistry.load()


def _display_order(output: Any, prefs: tuple[str, ...]) -> list[str]:
    water_group = {
        WaterFeasibility.FEASIBLE: 0,
        WaterFeasibility.RISKY: 1,
        WaterFeasibility.UNKNOWN: 1,
        WaterFeasibility.NOT_FEASIBLE: 2,
    }

    def key(r: Any) -> tuple[int, int, int]:
        rot = CATALOG_BY_ID.get(r.rotation_id)
        is_double = bool(rot and any(c.is_double_crop for c in rot.campaigns))
        return (
            water_group[r.water_feasibility] if "WATER_SAFE_FIRST" in prefs else 0,
            (0 if is_double else 1) if "DOUBLE_CROP_FIRST" in prefs else 0,
            r.rank,
        )

    return [r.rotation_id for r in sorted(output.results, key=key)]


def _evaluate_lite(req: LiteEvaluateRequest) -> dict[str, Any]:
    if req.plot_id != DEMO_PLOT_ID:
        raise ApiError(
            ErrorCode.PLOT_NOT_FOUND, f"lote '{req.plot_id}' sin datos cacheados en el MVP"
        )
    if req.actor not in PROFILE_ASSUMPTIONS:
        raise ApiError(
            ErrorCode.UNKNOWN_ACTOR,
            f"actor '{req.actor}' desconocido",
            {"allowed": sorted(PROFILE_ASSUMPTIONS)},
        )
    current = req.current_rotation
    if current is None:
        if req.current_rotation_id not in CATALOG_BY_ID:
            raise ApiError(
                ErrorCode.UNKNOWN_ROTATION,
                f"rotación '{req.current_rotation_id}' fuera del catálogo",
                {"allowed": sorted(CATALOG_BY_ID)},
            )
        current = CATALOG_BY_ID[req.current_rotation_id]
    reg = _registry()
    ov = req.overrides or ProfileOverrides()
    try:
        profile = actor_profile(
            reg,
            req.actor,
            horizon_years=ov.horizon_years,
            alpha=ov.alpha,
            risk_aversion=ov.risk_aversion,
            discount_rate=ov.discount_rate,
            priorities=ov.priorities,
            machinery_windows=ov.machinery_windows,
        )
    except ValueError as exc:
        raise ApiError(ErrorCode.VALIDATION_ERROR, str(exc)) from exc
    try:
        inp = build_engine_input(
            profile, current_rotation=current, year_class_filter=req.year_class_filter, registry=reg
        )
    except DataError as exc:
        raise ApiError(ErrorCode.DATA_UNAVAILABLE, str(exc)) from exc
    out = evaluate(inp)
    names = {r.rotation_id: r.name for r in (*CATALOG, current)}
    exp = explain(out, names)
    sowing = sowing_decision(
        out, names, reg, demo_economics(reg), req.rent_qq_ha, req.fallow_cost_usd_ha
    )
    return {
        "sowing": sowing.model_dump(mode="json"),
        "explanation": exp.model_dump(mode="json"),
        "explanation_text": render_web(exp),
        "input_hash": out.input_hash,
        "engine_version": out.engine_version,
        "engine_output": out.model_dump(mode="json"),
        "rotation_names": names,
        "display_order": _display_order(out, req.display_preferences),
        "resolution": [
            {
                "part": "climate",
                "origin": "CACHE",
                "source_ref": "NASA_POWER daily point 1981-2025",
            },
            {
                "part": "economics",
                "origin": "ASSUMPTION",
                "assumption_ids": ["A-DEMO-02", "A-DEMO-03", "A-DEMO-04", "A-DEMO-05", "A-DEMO-06"],
            },
            {"part": "soil", "origin": "ASSUMPTION", "assumption_ids": ["A-DEMO-07", "A-WAT-14"]},
            {"part": "initial_moisture", "origin": "MISSING", "assumption_ids": ["A-WAT-12"]},
            {
                "part": "profile",
                "origin": "ASSUMPTION" if req.overrides is None else "USER_INPUT",
                "assumption_ids": [PROFILE_ASSUMPTIONS[req.actor]],
            },
        ],
    }


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    cfg = settings or ApiSettings()
    app = FastAPI(
        title="Rastrojo API",
        version=__version__,
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in cfg.cors_allowed_origins.split(",") if o.strip()],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Input-Hash", "X-Engine-Version"],
    )

    @app.middleware("http")
    async def body_limit(request: Request, call_next: Any) -> Response:
        length = request.headers.get("content-length")
        if length is not None and int(length) > cfg.max_body_bytes:
            return error_response(
                ErrorCode.PAYLOAD_TOO_LARGE, f"el cuerpo supera {cfg.max_body_bytes} bytes"
            )
        if request.method == "POST" and not request.headers.get("content-type", "").startswith(
            "application/json"
        ):
            return error_response(ErrorCode.UNSUPPORTED_MEDIA_TYPE, "se espera application/json")
        response: Response = await call_next(request)
        return response

    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError) -> Response:
        return error_response(exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> Response:
        details = [
            {"loc": [str(x) for x in e.get("loc", ())], "msg": e.get("msg", "")}
            for e in exc.errors()
        ]
        return error_response(ErrorCode.VALIDATION_ERROR, "la solicitud no es válida", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> Response:
        if exc.status_code == 405:
            return error_response(ErrorCode.METHOD_NOT_ALLOWED, "método no permitido")
        return error_response(ErrorCode.NOT_FOUND, "recurso no encontrado")

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception) -> Response:
        return error_response(
            ErrorCode.INTERNAL_ERROR, "error interno", {"type": type(exc).__name__}
        )

    @app.get(f"{API_PREFIX}/health")
    async def health() -> Response:
        return canonical_response(
            {
                "status": "demo" if cfg.demo_mode else "ok",
                "engine_version": ENGINE_VERSION,
                "api_version": __version__,
                "datasets": {
                    "NASA_POWER": "FIXTURE",
                    "SMAP_L4": "EMPTY",
                    "GPM_IMERG": "EMPTY",
                    "GRACE_FO": "EMPTY",
                    "MODIS_NDVI": "EMPTY",
                },
            }
        )

    @app.get(f"{API_PREFIX}/rotations/catalog")
    async def catalog() -> Response:
        return canonical_response({"rotations": [r.model_dump(mode="json") for r in CATALOG]})

    @app.get(f"{API_PREFIX}/actors/profiles")
    async def profiles() -> Response:
        reg = _registry()
        return canonical_response(
            {
                "profiles": [
                    actor_profile(reg, pid).model_dump(mode="json") for pid in PROFILE_ASSUMPTIONS
                ],
                "slider_limits": reg.value("A-ACT-06"),
            }
        )

    @app.post(f"{API_PREFIX}/ask")
    async def ask(req: AskRequest) -> Response:
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(respond, req), timeout=cfg.engine_timeout_s
            )
        except TimeoutError as exc:
            raise ApiError(
                ErrorCode.TIMEOUT, f"la consulta superó {cfg.engine_timeout_s} s"
            ) from exc
        return canonical_response(resp.model_dump(mode="json"))

    @app.post(f"{API_PREFIX}/chat/simulate")
    async def chat_simulate(req: AskRequest) -> Response:
        resp = await asyncio.to_thread(respond, req.model_copy(update={"channel": "whatsapp"}))
        from rastrojo.application.explanations import partition

        body = resp.model_dump(mode="json")
        body["messages"] = partition(resp.text, tail=())
        return canonical_response(body)

    @app.get(f"{API_PREFIX}/glossary")
    async def glossary() -> Response:
        return canonical_response({"terms": load_glossary()})

    @app.get(f"{API_PREFIX}/assumptions")
    async def assumptions() -> Response:
        reg = _registry()
        return canonical_response(
            {"assumptions": [reg.get(a).model_dump(mode="json") for a in reg.ids()]}
        )

    @app.post(f"{API_PREFIX}/evaluate")
    async def evaluate_endpoint(req: LiteEvaluateRequest) -> Response:
        try:
            payload = await asyncio.wait_for(
                asyncio.to_thread(_evaluate_lite, req), timeout=cfg.engine_timeout_s
            )
        except TimeoutError as exc:
            raise ApiError(
                ErrorCode.TIMEOUT, f"la evaluación superó {cfg.engine_timeout_s} s"
            ) from exc
        return canonical_response(
            payload,
            headers={
                "X-Input-Hash": payload["input_hash"],
                "X-Engine-Version": payload["engine_version"],
            },
        )

    return app


app = create_app()
