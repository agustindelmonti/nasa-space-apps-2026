"""Exporta el JSON Schema de los contratos del motor a schemas/.

Uso: `uv run python scripts/export_schemas.py` (escribe) o `--check` (falla si hay diff).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import BaseModel

from rastrojo.domain import EngineInput, EngineOutput

ROOT = Path(__file__).resolve().parents[1]
TARGETS: dict[str, type[BaseModel]] = {
    "engine_input.schema.json": EngineInput,
    "engine_output.schema.json": EngineOutput,
}


def render(model: type[BaseModel]) -> str:
    return (
        json.dumps(model.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )


def main() -> int:
    check = "--check" in sys.argv
    out_dir = ROOT / "schemas"
    out_dir.mkdir(exist_ok=True)
    stale = []
    for name, model in TARGETS.items():
        path = out_dir / name
        content = render(model)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            path.write_text(content, encoding="utf-8")
    if stale:
        print(f"Schemas desactualizados: {', '.join(stale)}. Corré scripts/export_schemas.py")
        return 1
    print("OK" if check else f"Escritos {len(TARGETS)} schemas en {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
