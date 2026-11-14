"""Entrada de la Vercel Function de Python: expone la API FastAPI de Rastrojo bajo /api/*.

Corre sin pandas: el clima del lote demo sale de data/fixtures/demo/engine_climate.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rastrojo.adapters.api import app  # noqa: E402

__all__ = ["app"]
