"""EngineInput del lote demo armado desde el fixture real de POWER (sin red)."""

from __future__ import annotations

from functools import lru_cache

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import actor_profile, build_engine_input
from rastrojo.domain import ActorProfile, EngineInput, Rotation, YearClassFilter


@lru_cache(maxsize=1)
def registry() -> AssumptionRegistry:
    return AssumptionRegistry.load()


def profile(pid: str = "OWNER", **kw) -> ActorProfile:
    return actor_profile(registry(), pid, **kw)


def demo_input(
    p: ActorProfile | None = None,
    current: Rotation | None = None,
    year_class_filter: YearClassFilter = YearClassFilter.ALL,
) -> EngineInput:
    return build_engine_input(
        p or profile(),
        current_rotation=current,
        year_class_filter=year_class_filter,
        registry=registry(),
    )
