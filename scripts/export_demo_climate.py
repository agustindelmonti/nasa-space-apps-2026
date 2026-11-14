"""Genera data/fixtures/demo/engine_climate.json desde la caché/fixture de NASA POWER.

Uso: `uv run python scripts/export_demo_climate.py`
"""

from __future__ import annotations

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import CLIMATE_SNAPSHOT, demo_plot, export_snapshot


def main() -> None:
    plot = demo_plot(AssumptionRegistry.load())
    snap = export_snapshot(plot.location.lat, plot.location.lon)
    CLIMATE_SNAPSHOT.write_text(snap.model_dump_json(), encoding="utf-8")
    print(
        f"{CLIMATE_SNAPSHOT} ({CLIMATE_SNAPSHOT.stat().st_size // 1024} KB, {len(snap.scenarios)} escenarios)"
    )


if __name__ == "__main__":
    main()
