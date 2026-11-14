"""Registro de huecos: cada faltante con dataset, variable, fecha y motivo.

Nada de interpolar ni rellenar: estas funciones solo cuentan y listan lo que falta.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from pydantic import BaseModel, ConfigDict


class GapEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    variable: str
    date: date
    reason: str


class GapReport(BaseModel):
    """Conteo de faltantes por variable y por año, más la lista de fechas afectadas."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset: str
    total_days: int
    missing_by_variable: dict[str, int]
    missing_by_year: dict[int, dict[str, int]]
    entries: tuple[GapEntry, ...]

    @property
    def has_gaps(self) -> bool:
        return any(n > 0 for n in self.missing_by_variable.values())


def missing_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla año x variable con la cantidad de días faltantes (incluye ceros)."""
    years = pd.to_datetime(df["date"]).dt.year
    table = (
        df.assign(year=years, missing=df["is_missing"].astype(int))
        .pivot_table(index="year", columns="variable", values="missing", aggfunc="sum")
        .fillna(0)
        .astype(int)
        .sort_index()
    )
    table.columns.name = None
    return table


def gap_report(df: pd.DataFrame, dataset: str) -> GapReport:
    ordered = df.sort_values(["variable", "date"], kind="mergesort")
    totals = {
        str(var): int(group["is_missing"].sum())
        for var, group in ordered.groupby("variable", sort=True)
    }
    by_year_table = missing_by_year(ordered)
    by_year = {
        int(year): {str(col): int(n) for col, n in zip(by_year_table.columns, row, strict=True)}
        for year, row in zip(
            by_year_table.index.tolist(), by_year_table.to_numpy().tolist(), strict=True
        )
    }
    missing = ordered[ordered["is_missing"]]
    entries = tuple(
        GapEntry(variable=str(v), date=pd.Timestamp(d).date(), reason=str(r))
        for v, d, r in zip(
            missing["variable"], missing["date"], missing["missing_reason"], strict=True
        )
    )
    total_days = int(ordered["date"].nunique())
    return GapReport(
        dataset=dataset,
        total_days=total_days,
        missing_by_variable=totals,
        missing_by_year=by_year,
        entries=entries,
    )
