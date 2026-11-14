"""Errores tipados de la capa de datos.

La API los traduce a ``{code, message, details}``; por eso cada error lleva un código
estable y un diccionario de detalles serializable.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class DataErrorCode(StrEnum):
    PERIOD_OUT_OF_COVERAGE = "PERIOD_OUT_OF_COVERAGE"
    DATA_NOT_CACHED = "DATA_NOT_CACHED"
    EARTHDATA_AUTH_MISSING = "EARTHDATA_AUTH_MISSING"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    CACHE_SCHEMA_INVALID = "CACHE_SCHEMA_INVALID"
    SOURCE_INCOMPLETE = "SOURCE_INCOMPLETE"


class DataError(Exception):
    """Error de ingesta o caché con código tipado."""

    def __init__(self, code: DataErrorCode, message: str, **details: Any) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.message = message
        self.details: dict[str, Any] = details

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code.value, "message": self.message, "details": self.details}
