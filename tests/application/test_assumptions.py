from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from rastrojo.application.assumptions import (
    AssumptionNotFoundError,
    AssumptionRegistry,
    climate_config,
)


def test_registry_loads_and_resolves_climate_config() -> None:
    reg = AssumptionRegistry.load()
    cfg = climate_config(reg)
    assert cfg.summer.bounds(2008) == (date(2008, 11, 1), date(2009, 3, 31))
    assert cfg.min_years == 15 and cfg.max_missing_days == 0
    assert reg.get("A-CLI-01").status.value == "PENDING_AFA"


def test_window_changed_by_agronomists(tmp_path: Path) -> None:
    text = Path("data/assumptions.yaml").read_text(encoding="utf-8")
    edited = text.replace('end: "10-31"', 'end: "09-30"')
    p = tmp_path / "a.yaml"
    p.write_text(edited, encoding="utf-8")
    cfg = climate_config(AssumptionRegistry.load(p))
    assert cfg.winter.bounds(2010)[1] == date(2010, 9, 30)
    assert "A-CLI-01" in cfg.assumption_ids


def test_missing_assumption() -> None:
    with pytest.raises(AssumptionNotFoundError):
        AssumptionRegistry.load().get("A-CLI-99")
