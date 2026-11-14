"""Esquemas pandera de la caché en formato largo.

Formato largo (una fila por fecha y variable) para que el registro de huecos sea una
consulta y no una convención: ``date``, ``variable``, ``value``, ``unit``, ``is_missing``,
``missing_reason``. Los rangos físicos son límites de plausibilidad para detectar
archivos corruptos o unidades equivocadas, no valores agronómicos.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import pandas as pd
import pandera.errors as pa_errors
import pandera.pandas as pa

from rastrojo.data.errors import DataError, DataErrorCode

LONG_COLUMNS: tuple[str, ...] = (
    "date",
    "variable",
    "value",
    "unit",
    "is_missing",
    "missing_reason",
)


class MissingReason(StrEnum):
    """Motivos de hueco. Un faltante nunca se rellena: queda registrado con su motivo."""

    FILL_VALUE = "FILL_VALUE"  # el producto publicó su valor de relleno (POWER: -999)
    NO_DATA = "NO_DATA"  # la fecha o la variable no vino en la respuesta
    MISSING_INPUT = "MISSING_INPUT"  # valor derivado sin todos sus insumos
    NOT_YET_PUBLISHED = "NOT_YET_PUBLISHED"
    MISSION_GAP = "MISSION_GAP"
    QA_REJECTED = "QA_REJECTED"


@dataclass(frozen=True)
class VariableSpec:
    """Unidad declarada y rango físico plausible de una variable."""

    unit: str
    min_value: float
    max_value: float


@dataclass(frozen=True)
class DatasetSchemaSpec:
    dataset: str
    variables: dict[str, VariableSpec]


def _range_check(variable: str, spec: VariableSpec) -> pa.Check:
    def check(df: pd.DataFrame) -> pd.Series[bool]:
        mask = df["variable"] != variable
        in_range = df["value"].between(spec.min_value, spec.max_value)
        return mask | df["value"].isna() | in_range

    return pa.Check(
        check,
        name=f"range_{variable}",
        error=(
            f"{variable} fuera del rango físico permitido "
            f"[{spec.min_value}, {spec.max_value}] {spec.unit}"
        ),
    )


def _unit_check(variable: str, spec: VariableSpec) -> pa.Check:
    def check(df: pd.DataFrame) -> pd.Series[bool]:
        return (df["variable"] != variable) | (df["unit"] == spec.unit)

    return pa.Check(check, name=f"unit_{variable}", error=f"{variable} debe estar en {spec.unit}")


def _missing_consistency(df: pd.DataFrame) -> pd.Series[bool]:
    value_na = df["value"].isna()
    reason_na = df["missing_reason"].isna()
    return (df["is_missing"] == value_na) & (df["is_missing"] != reason_na)


def build_schema(spec: DatasetSchemaSpec) -> pa.DataFrameSchema:
    checks: list[pa.Check] = [
        pa.Check(
            _missing_consistency,
            name="missing_consistency",
            error="is_missing debe coincidir con value nulo y con missing_reason presente",
        )
    ]
    for variable, vspec in spec.variables.items():
        checks.append(_range_check(variable, vspec))
        checks.append(_unit_check(variable, vspec))
    reasons = [r.value for r in MissingReason]
    return pa.DataFrameSchema(
        columns={
            "date": pa.Column("datetime64[ns]", nullable=False),
            "variable": pa.Column(str, pa.Check.isin(list(spec.variables)), nullable=False),
            "value": pa.Column(float, nullable=True),
            "unit": pa.Column(str, nullable=False),
            "is_missing": pa.Column(bool, nullable=False),
            "missing_reason": pa.Column(str, pa.Check.isin(reasons), nullable=True),
        },
        checks=checks,
        unique=["variable", "date"],
        strict=True,
        ordered=True,
        name=spec.dataset,
    )


def validate_long(
    df: pd.DataFrame, spec: DatasetSchemaSpec, *, required: tuple[str, ...] | None = None
) -> pd.DataFrame:
    """Valida un frame largo; ante cualquier falla lanza ``CACHE_SCHEMA_INVALID``.

    ``required`` lista las variables que tienen que estar presentes (por defecto todas
    las del esquema). Una variable ausente se informa por nombre en el error.
    """
    missing_cols = [c for c in LONG_COLUMNS if c not in df.columns]
    if missing_cols:
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"faltan columnas en la caché de {spec.dataset}: {', '.join(missing_cols)}",
            dataset=spec.dataset,
            missing_columns=missing_cols,
        )
    expected = required if required is not None else tuple(spec.variables)
    present = set(df["variable"].unique().tolist())
    missing_vars = [v for v in expected if v not in present]
    if missing_vars:
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"faltan variables en la caché de {spec.dataset}: {', '.join(missing_vars)}",
            dataset=spec.dataset,
            missing_variables=missing_vars,
        )
    try:
        validated: pd.DataFrame = build_schema(spec).validate(df, lazy=True)
    except pa_errors.SchemaErrors as exc:
        failures: list[dict[str, Any]] = (
            exc.failure_cases[["column", "check"]]
            .drop_duplicates()
            .astype(str)
            .to_dict(orient="records")
        )
        checks = sorted({f["check"] for f in failures})
        raise DataError(
            DataErrorCode.CACHE_SCHEMA_INVALID,
            f"la caché de {spec.dataset} no cumple el esquema: {'; '.join(checks)}",
            dataset=spec.dataset,
            failures=failures,
        ) from exc
    return validated
