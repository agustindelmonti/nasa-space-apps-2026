"""Precalcula la búsqueda exhaustiva de rotaciones para los perfiles predefinidos.

Uso: ``uv run python scripts/precompute_search.py [--workers 4] [--only OWNER_ALL]``

Corre ``rastrojo.application.search.run_search`` para OWNER, TENANT, COOP y BANK con los
filtros de año ALL, DRY, NORMAL y WET (16 búsquedas de ~1 minuto cada una) y escribe
``data/fixtures/demo/search/<actor>_<filtro>.json``. Usa el snapshot de clima del demo, así que
debe correr después de regenerarlo. Determinista: misma entrada, mismo archivo.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

from rastrojo.application.assumptions import AssumptionRegistry
from rastrojo.application.demo import PROFILE_ASSUMPTIONS, actor_profile, build_engine_input
from rastrojo.application.search import SEARCH_DIR, run_search
from rastrojo.domain.climate import YearClassFilter

OUT_DIR = SEARCH_DIR


def one(actor: str, flt: str) -> tuple[str, float]:
    t0 = time.perf_counter()
    reg = AssumptionRegistry.load()
    inp = build_engine_input(
        actor_profile(reg, actor), year_class_filter=YearClassFilter(flt), registry=reg
    )
    result = run_search(inp, reg)
    path = OUT_DIR / f"{actor}_{flt}.json"
    path.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return path.name, time.perf_counter() - t0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--only", default="", help="un solo par, por ejemplo OWNER_ALL")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = [(a, f.value) for a in PROFILE_ASSUMPTIONS for f in YearClassFilter]
    if args.only:
        jobs = [j for j in jobs if f"{j[0]}_{j[1]}" == args.only]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for name, secs in pool.map(one, *zip(*jobs, strict=True)):
            print(f"{name}: {secs:.0f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
