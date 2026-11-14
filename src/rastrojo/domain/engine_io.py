"""Sobres de entrada y salida del motor, con hash canónico de la entrada."""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field, JsonValue, model_validator

from rastrojo.domain.actor import ActorProfile
from rastrojo.domain.base import DomainModel
from rastrojo.domain.canonical import canonical_json, sha256_hex
from rastrojo.domain.climate import ClimateScenario, WaterInputs, YearClassFilter, check_weights
from rastrojo.domain.crops import Rotation
from rastrojo.domain.economics import EconomicParameters
from rastrojo.domain.plot import Plot, Soil
from rastrojo.domain.provenance import AssumptionId
from rastrojo.domain.results import RotationResult

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ResolvedAssumption(DomainModel):
    """Valor de un supuesto tal como se usó en esta evaluación (copiado del registro)."""

    value: JsonValue
    unit: str | None = None


class EngineInput(DomainModel):
    plot: Plot
    soil: Soil
    current_rotation: Rotation
    candidates: tuple[Rotation, ...] = Field(min_length=1)
    profile: ActorProfile
    economics: EconomicParameters
    scenarios: tuple[ClimateScenario, ...] = Field(min_length=1)
    resolved_assumptions: dict[AssumptionId, ResolvedAssumption]
    water_inputs: WaterInputs
    year_class_filter: YearClassFilter = YearClassFilter.ALL

    @model_validator(mode="after")
    def _checks(self) -> EngineInput:
        ids = [r.rotation_id for r in self.candidates]
        if len(set(ids)) != len(ids):
            raise ValueError("hay rotaciones candidatas con id repetido")
        check_weights(self.scenarios)
        years = [s.campaign_start_year for s in self.scenarios]
        if len(set(years)) != len(years):
            raise ValueError("hay escenarios con año repetido")
        weather_years = {w.campaign_start_year for w in self.water_inputs.weather}
        missing = sorted(set(years) - weather_years)
        if missing:
            raise ValueError(f"faltan series diarias para los años: {missing}")
        return self

    def canonical_data(self) -> dict[str, Any]:
        """Datos para el hash: candidatas por id y escenarios/series por año."""
        data: dict[str, Any] = self.model_dump(mode="json")
        data["candidates"] = sorted(data["candidates"], key=lambda r: r["rotation_id"])
        data["scenarios"] = sorted(data["scenarios"], key=lambda s: s["campaign_start_year"])
        data["water_inputs"]["weather"] = sorted(
            data["water_inputs"]["weather"], key=lambda w: w["campaign_start_year"]
        )
        return data

    def canonical_bytes(self) -> bytes:
        return canonical_json(self.canonical_data())

    def input_hash(self) -> str:
        return sha256_hex(self.canonical_bytes())


class EngineOutput(DomainModel):
    engine_version: str = Field(min_length=1)
    input_hash: str
    results: tuple[RotationResult, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _checks(self) -> EngineOutput:
        if not _HEX64.fullmatch(self.input_hash):
            raise ValueError("input_hash debe ser un SHA-256 en hexadecimal (64 caracteres)")
        ranks = [r.rank for r in self.results]
        if ranks != list(range(1, len(self.results) + 1)):
            raise ValueError("los resultados deben venir ordenados por rango 1..n sin huecos")
        current = [r for r in self.results if r.is_current]
        if len(current) != 1:
            raise ValueError("debe haber exactamente una rotación marcada como actual")
        base = current[0].score
        for r in self.results:
            expected = r.score - base
            if abs(r.score_delta_vs_current.value - expected) > 1e-6 * max(1.0, abs(expected)):
                raise ValueError(
                    f"score_delta_vs_current de {r.rotation_id} no coincide "
                    "con la diferencia de puntaje"
                )
        return self

    def canonical_bytes(self) -> bytes:
        return canonical_json(self)
