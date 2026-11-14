# Proposal: quality

**Prioridad:** P0 para determinismo, test de imports, CI mínimo (ruff + pytest), test de UNKNOWN distinto de no factible, lenguaje prohibido (incluido "% de confianza") en todas las salidas, entregables `AI_USE.md` y `PRIOR_WORK.md` y fuente de cada número del pitch y la página NASA; P1 para property tests, snapshots, cobertura, mypy estricto, preferencias de presentación sin efecto en el motor y chequeo documentado de años secos contra MAGyP; P2 para endurecer el CI (matriz, caché).

## Why

La promesa central ante el jurado y AFA es "misma entrada, misma salida, todo trazable". Eso solo vale si se verifica automáticamente en cada push: determinismo byte a byte, propiedades del ranking que un agrónomo daría por obvias, snapshots del lote demo y una barrera que impida que el motor importe red, reloj o random. Con un equipo trabajando en paralelo durante 30 horas, el CI es lo que evita romper la demo el domingo a las 14.

## What Changes

- Test de determinismo: dos corridas en el mismo proceso y en procesos separados (con distinto `PYTHONHASHSEED`) comparan bytes del JSON canónico.
- Property tests con hypothesis sobre el ranking: λ, α, permutación de candidatas y escala monetaria.
- Snapshot tests del lote demo por perfil, con regla de bump de `engine_version` si el snapshot cambia.
- Cobertura mínima del paquete engine (90 %) y de domain.
- ruff (lint + format) en todo el repo y mypy estricto en engine y domain.
- Test estático de imports: engine no importa módulos de red, tiempo, random, sistema ni capas superiores.
- Test de que datos insuficientes producen factibilidad UNKNOWN y nunca NOT_FEASIBLE.
- Test de lenguaje sobre explicaciones, textos de la web y material del pitch con la lista prohibida de explanations ("% de confianza", "predice", "garantiza", entre otras).
- Verificación de entregables de transparencia: `AI_USE.md` y `PRIOR_WORK.md` en la raíz (los crea el ingeniero principal; quality solo exige su presencia y el enlace desde el README) y tabla número → dataset → archivo para cada cifra del pitch y de la página NASA.
- Test de que las preferencias de presentación no cambian salida del motor ni `input_hash`, y de que el chequeo MAGyP está documentado con fuentes (P1).
- Workflow de GitHub Actions que corre todo lo anterior sin red ni secretos.

## Capabilities

### New Capabilities
- `quality`: garantías verificables automáticamente de determinismo, pureza, propiedades del ranking, regresión del lote demo y calidad estática.

### Modified Capabilities
- Ninguna.

## Impact

- `tests/` (unit, property, snapshot, determinism, architecture), `pyproject.toml` (config de ruff, mypy, pytest, coverage), `.github/workflows/ci.yml`.
- Dependencias de desarrollo: pytest, hypothesis, pytest-cov, syrupy (snapshots), ruff, mypy.
- Afecta a todos los changes del engine: sus tests corren en este CI.

## Fuera de alcance

- Tests end-to-end del front y de WhatsApp contra Twilio (los cubren web-demo y whatsapp-channel con mocks).
- Tests de carga o performance.
- Validación agronómica de resultados (es trabajo con AFA, no automatizable).
- Deploy continuo (lo define api / web-demo).
