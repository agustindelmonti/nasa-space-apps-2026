# Design: quality

## Context

Ver proposal.md. Repo Python 3.12 con uv, paquete `fieldshift`. El motor es puro (rotation-engine) y serializa con el JSON canónico de domain-models. Los fixtures del lote demo los produce demo-mode en `data/fixtures/demo/`.

## Goals / Non-Goals

**Goals:** CI en menos de 5 minutos, sin red ni secretos; fallas con mensajes que digan qué se rompió; propiedades formuladas para no dar falsos positivos por redondeo.

**Non-Goals:** mutation testing, fuzzing de la API, tests de navegador.

## Decisions

### 1. Layout de tests

```
tests/
  domain/            unit de modelos
  engine/            unit por módulo (economics, soil, risk, ranking)
  property/          hypothesis (estrategias compartidas en strategies.py)
  snapshots/         syrupy, un snapshot por perfil del lote demo
  determinism/       mismo proceso y subprocesos
  architecture/      test de imports por AST
  demo/              rankings distintos (actor-profiles)
```

Marcadores pytest: `network` (excluido en CI con `-m "not network"`), `slow`.

### 2. Determinismo

- Mismo proceso: `canonical_bytes(evaluate(inp))` dos veces por perfil; en falla, se calcula la primera ruta JSON distinta con un diff recursivo propio (sin dependencias).
- Entre procesos: `subprocess.run([sys.executable, "-m", "fieldshift.engine.cli_eval", path], env={"PYTHONHASHSEED": s, "PATH": ...})` con s ∈ {1, 2}; el módulo `cli_eval` lee un archivo y escribe a stdout (vive fuera de engine, en `fieldshift.tools`, para no meter I/O en el motor). Se compara SHA-256 de stdout.

### 3. Estrategias de hypothesis

- `engine_inputs()`: elige 1 a 6 candidatas del catálogo, 3 a 40 escenarios con pesos uniformes y clases anual y por estación, parámetros económicos positivos acotados, insumos hídricos sintéticos por escenario (series diarias cortas de lluvia, ET0 y temperaturas; el estado hídrico ya no se genera porque lo calcula el motor), perfil dentro de A-ACT-06 con prioridades opcionales. Todo generado en floats "amigables" (múltiplos de 0.01) para reducir ruido.
- `settings(max_examples=200, deadline=None, derandomize=True)`: `derandomize` hace reproducibles las corridas en CI.
- Propiedades sobre puntajes sin redondear (expuestos en el desglose con precisión completa en memoria); la de α excluye casos con diferencias < 0.01 USD/ha porque el desempate por Riesgo puede reordenar empates de redondeo.
- Escala monetaria: se escalan todos los campos monetarios, incluidos el capital máximo del actor y los κ de prioridades (A-ACT-08, A-ACT-09); si no se escalara, el filtro de capital cambiaría la elegibilidad y la propiedad sería falsa por construcción. "Precios" en el pedido original se interpreta como todos los valores monetarios.

### 4. Snapshots y versión

syrupy con extensión JSON sobre los bytes canónicos. Test de coherencia: un archivo `tests/snapshots/engine_version.lock` guarda la versión con la que se generaron; si el contenido de algún snapshot difiere del commit base y la versión es igual, falla. Implementación simple: el lock guarda también el SHA-256 de cada snapshot; cambia un hash sin cambiar la versión → falla.

### 5. Test de imports (AST)

Recorre `src/fieldshift/engine/**/*.py` con `ast.parse` y revisa `Import` / `ImportFrom`.

- Prohibidos (prefijo del módulo): `socket`, `ssl`, `http`, `urllib`, `requests`, `httpx`, `aiohttp`, `ftplib`, `smtplib`, `time`, `random`, `secrets`, `uuid`, `os`, `sys`, `subprocess`, `shutil`, `pathlib`, `io`, `tempfile`, `threading`, `multiprocessing`, `asyncio`, `concurrent`, `anthropic`, `openai`, `twilio`, `earthaccess`, `pandas`, `xarray`, `fieldshift.data`, `fieldshift.application`, `fieldshift.adapters`.
- `datetime` se permite solo como `from datetime import date`; cualquier llamada a atributos `now`, `today`, `utcnow` falla.
- Permitidos: `math`, `dataclasses`, `enum`, `typing`, `collections`, `itertools`, `functools`, `decimal`, `fractions`, `hashlib`, `json`, `fieldshift.domain`, `fieldshift.engine`.
- Se usa lista de prohibidos + lista de permitidos: un módulo no listado falla con mensaje "agregar a una de las listas", para forzar la decisión explícita.

Alternativa descartada: import-linter. Útil para capas, pero no detecta llamadas a `now()` y agrega configuración; el test AST es ~60 líneas.

### 6. CI (GitHub Actions)

`.github/workflows/ci.yml`, `on: [push, pull_request]`, `ubuntu-latest`, `astral-sh/setup-uv` con versión fijada, Python 3.12.

```
jobs:
  lint:   uv sync --frozen; uv run ruff check .; uv run ruff format --check .
  types:  uv run mypy --strict src/fieldshift/engine src/fieldshift/domain
  test:   uv run pytest -m "not network" --cov=fieldshift.engine --cov=fieldshift.domain
          --cov-branch --cov-fail-under=90
```

El umbral de 90 % se aplica al total de engine + domain (pytest-cov no separa umbrales por paquete); un paso extra con `coverage report --include="src/fieldshift/engine/*" --fail-under=90` asegura el de engine solo. `permissions: contents: read`, sin secretos. Las acciones se fijan por versión.

### Alternativas descartadas

- **Tox / nox:** uv ya resuelve entornos; una capa más no paga en 30 horas.
- **Cobertura 100 %:** induce tests vacíos bajo presión de tiempo.
- **pre-commit obligatorio:** se recomienda localmente, pero el CI es la fuente de verdad (no todos los integrantes lo van a instalar).

## Risks / Trade-offs

- [hypothesis encuentra bordes de redondeo y bloquea el CI el domingo] → `derandomize=True`, propiedades sobre valores sin redondear y exclusión explícita de empates por debajo de 0.01.
- [Snapshots que se actualizan en masa sin mirar] → regla de bump de versión y diff visible en el PR.
- [CI lento] → un solo `uv sync` con caché de uv; property tests con 200 ejemplos.

## Open Questions

- ¿Hay que correr también en Windows/macOS para el determinismo entre plataformas? P2; el redondeo canónico debería absorberlo.
