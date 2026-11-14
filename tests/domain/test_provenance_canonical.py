from __future__ import annotations

import json
import math
from datetime import date

import pytest
from pydantic import ValidationError

from rastrojo.domain import (
    Assumption,
    AssumptionProvenance,
    AssumptionStatus,
    CanonicalizationError,
    Dataset,
    DerivedProvenance,
    ObservedProvenance,
    Period,
    PValue,
    Source,
    canonical_json,
)
from tests.domain.factories import engine_input, power_source, profile, pv


# Requirement: Valor con procedencia
def test_observed_without_source_fails() -> None:
    with pytest.raises(ValidationError):
        PValue.model_validate({"value": 1, "unit": "mm", "provenance": {"kind": "OBSERVED"}})


def test_assumption_without_id_fails() -> None:
    with pytest.raises(ValidationError):
        PValue.model_validate({"value": 1, "unit": "mm", "provenance": {"kind": "ASSUMPTION"}})


def test_derived_lists_inputs_and_method() -> None:
    v = pv(
        12.5,
        "mm",
        DerivedProvenance(
            method="balance bucket FAO-56", derived_from=("NASA_POWER:ET0", "A-WAT-01")
        ),
    )
    dumped = json.loads(canonical_json(v))
    assert dumped["provenance"]["derived_from"] == ["NASA_POWER:ET0", "A-WAT-01"]
    assert dumped["provenance"]["method"] == "balance bucket FAO-56"


def test_unknown_field_rejected_with_name() -> None:
    with pytest.raises(ValidationError, match="color"):
        PValue.model_validate(
            {"value": 1, "unit": "mm", "provenance": {"kind": "USER_INPUT"}, "color": "red"}
        )


# Requirement: Fuente de datos descriptiva / productos modelados
def test_soilgrids_is_observed_and_modeled() -> None:
    src = Source(
        dataset=Dataset.SOILGRIDS,
        variable="clay",
        period=Period(start=date(2020, 1, 1), end=date(2020, 1, 1)),
        spatial_resolution="250 m",
        temporal_resolution="estático",
        is_modeled=True,
    )
    v = pv(25, "%", ObservedProvenance(source=src))
    assert v.provenance.kind == "OBSERVED"
    assert v.provenance.source.is_modeled is True


@pytest.mark.parametrize("ds", ["SRTM", "ECOSTRESS", "GLDAS", "FIELD_HAMMER"])
def test_new_datasets_accepted(ds: str) -> None:
    src = power_source().model_copy(update={"dataset": Dataset(ds)})
    assert src.dataset.value == ds


def test_unknown_assumption_area_lists_allowed() -> None:
    with pytest.raises(ValidationError, match="DEMO"):
        AssumptionProvenance(assumption_id="A-XYZ-01")


def test_assumption_id_format() -> None:
    with pytest.raises(ValidationError, match="A-<AREA>-<NN>"):
        AssumptionProvenance(assumption_id="kc-soja")


def test_smap_value_as_published_is_observed_modeled() -> None:
    src = Source(
        dataset=Dataset.SMAP_L4,
        variable="sm_rootzone",
        period=Period(start=date(2026, 11, 1), end=date(2026, 11, 1)),
        spatial_resolution="~9 km",
        temporal_resolution="3-horaria",
        is_modeled=True,
    )
    v = pv(0.27, "m3/m3", ObservedProvenance(source=src))
    assert v.provenance.kind == "OBSERVED" and v.provenance.source.is_modeled


def test_daily_mean_is_derived_from_observed() -> None:
    v = pv(
        0.26,
        "m3/m3",
        DerivedProvenance(method="media diaria", derived_from=("SMAP_L4:sm_rootzone",)),
    )
    assert v.provenance.kind == "DERIVED"


def test_assumption_registry_entry() -> None:
    a = Assumption(
        assumption_id="A-WAT-01",
        description="Kc por etapa",
        value={"SOY_1ST": 1.15},
        reference="FAO-56",
        status=AssumptionStatus.PENDING_AFA,
    )
    assert a.status is AssumptionStatus.PENDING_AFA


# Requirement: Serialización JSON canónica y hash
def test_nan_rejected_in_canonical_json() -> None:
    with pytest.raises(CanonicalizationError):
        canonical_json({"x": math.nan})


def test_nan_rejected_in_models() -> None:
    with pytest.raises(ValidationError):
        pv(math.nan, "mm")


def test_round_trip_stable() -> None:
    inp = engine_input()
    first = canonical_json(inp)
    again = canonical_json(json.loads(first))
    assert first == again


def test_hash_ignores_key_order() -> None:
    a = {"b": 1, "a": {"y": 2.0, "x": 1.0000001}}
    b = {"a": {"x": 1.0000001, "y": 2.0}, "b": 1}
    assert canonical_json(a) == canonical_json(b)


def test_hash_changes_with_lambda() -> None:
    base = engine_input()
    other = engine_input(profile=profile(risk_aversion_lambda=pv(0.9, "ratio")))
    assert base.input_hash() != other.input_hash()


def test_hash_reproducible_same_content() -> None:
    assert engine_input().input_hash() == engine_input().input_hash()
