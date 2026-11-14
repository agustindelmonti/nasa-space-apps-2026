"""Carga del registro de supuestos y resolución hacia configuraciones del motor."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from rastrojo.domain.provenance import Assumption
from rastrojo.engine.climate import ClassificationConfig, WindowDef

DEFAULT_REGISTRY = Path(__file__).resolve().parents[3] / "data" / "assumptions.yaml"


class AssumptionNotFoundError(KeyError):
    """Se pidió un supuesto que no está en el registro."""


class AssumptionRegistry:
    def __init__(self, entries: dict[str, Assumption]) -> None:
        self._entries = entries

    @classmethod
    def load(cls, path: Path = DEFAULT_REGISTRY) -> AssumptionRegistry:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        entries: dict[str, Assumption] = {}
        for item in raw:
            a = Assumption.model_validate(item)
            if a.assumption_id in entries:
                raise ValueError(f"supuesto duplicado en el registro: {a.assumption_id}")
            entries[a.assumption_id] = a
        return cls(entries)

    def get(self, assumption_id: str) -> Assumption:
        try:
            return self._entries[assumption_id]
        except KeyError as exc:
            raise AssumptionNotFoundError(assumption_id) from exc

    def value(self, assumption_id: str) -> Any:
        return self.get(assumption_id).value

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))


def _window(name: str, spec: dict[str, Any]) -> WindowDef:
    sm, sd = (int(x) for x in str(spec["start"]).split("-"))
    em, ed = (int(x) for x in str(spec["end"]).split("-"))
    return WindowDef(
        name=name,
        start_month=sm,
        start_day=sd,
        end_month=em,
        end_day=ed,
        crosses_year=bool(spec.get("crosses_year", False)),
    )


def climate_config(registry: AssumptionRegistry) -> ClassificationConfig:
    windows = registry.value("A-CLI-01")
    return ClassificationConfig(
        winter=_window("WINTER", windows["winter"]),
        summer=_window("SUMMER", windows["summer"]),
        max_missing_days=int(registry.value("A-CLI-02")),
        min_years=int(registry.value("A-CLI-03")),
        assumption_ids=("A-CLI-01", "A-CLI-02", "A-CLI-03"),
    )
