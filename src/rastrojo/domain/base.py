"""Base común de todos los modelos de dominio."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Modelo inmutable, sin campos extra y sin NaN ni infinitos.

    No usamos ``strict=True`` global: en modo Python impediría cargar fixtures YAML/JSON
    con enums y fechas como texto. La entrada de la API llega como JSON, donde Pydantic
    ya valida tipos con rigor; los rangos y unidades se validan explícitamente.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        allow_inf_nan=False,
        validate_default=True,
        use_enum_values=False,
    )
