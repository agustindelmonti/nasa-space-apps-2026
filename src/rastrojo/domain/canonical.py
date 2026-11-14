"""Serialización JSON canónica y hash SHA-256 reproducible."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from pydantic import BaseModel

DEFAULT_FLOAT_DIGITS = 6


class CanonicalizationError(ValueError):
    """Un valor no se puede serializar de forma canónica (NaN, infinito, tipo raro)."""


def _normalize(obj: Any, digits: int, path: str) -> Any:
    if isinstance(obj, bool) or obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise CanonicalizationError(f"valor no finito en '{path or '$'}': {obj!r}")
        rounded = round(obj, digits)
        return 0.0 if rounded == 0 else rounded
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"clave no textual en '{path or '$'}': {key!r}")
            out[key] = _normalize(value, digits, f"{path}.{key}")
        return out
    if isinstance(obj, list | tuple):
        return [_normalize(v, digits, f"{path}[{i}]") for i, v in enumerate(obj)]
    raise CanonicalizationError(f"tipo no serializable en '{path or '$'}': {type(obj).__name__}")


def to_canonical_data(
    obj: BaseModel | dict[str, Any] | list[Any], digits: int = DEFAULT_FLOAT_DIGITS
) -> Any:
    """Estructura JSON normalizada (floats redondeados, sin NaN)."""
    data = obj.model_dump(mode="json") if isinstance(obj, BaseModel) else obj
    return _normalize(data, digits, "")


def canonical_json(
    obj: BaseModel | dict[str, Any] | list[Any], digits: int = DEFAULT_FLOAT_DIGITS
) -> bytes:
    """UTF-8, claves ordenadas, sin espacios, floats redondeados, sin NaN ni infinitos."""
    data = to_canonical_data(obj, digits)
    text = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return text.encode("utf-8")


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
