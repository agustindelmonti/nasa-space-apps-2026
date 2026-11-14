# Proposal: demo-mode

**Prioridad:** P0 (fixtures del lote demo, DEMO_MODE=1 sin red, snapshot del motor, guion de 4 minutos con plan B para el sábado 19:00, confirmar en las bases oficiales las reglas de video y deck, guion del video parametrizado por duración con variante de 30 s, entregables `AI_USE.md` y `PRIOR_WORK.md`, página NASA y pitch con la fuente de cada número). P1: script de regeneración con diff, checklist automatizado completo. P2: material pulido para el video de YouTube.

## Why

La demo en vivo es un criterio de evaluación y la red de la sede, Earthdata y los deploys gratuitos pueden fallar justo en el pitch. Necesitamos que el lote de demo funcione igual con o sin internet, con datos NASA reales cacheados y trazables, un guion cronometrado y un plan B ensayado, sin esconder que los parámetros económicos son de ejemplo.

## What Changes

- Lote de demo `demo-casilda` (coordenadas placeholder del sur de Santa Fe, ASSUMPTION `A-DEMO-01` a confirmar con el equipo).
- Fixtures cacheados en `data/fixtures/demo/` para todos los datasets NASA usados (POWER, SMAP L4, GPM IMERG, GRACE-FO, MODIS NDVI, y SRTM y SoilGrids si se implementan en P1), con manifiesto de procedencia y checksums.
- Parámetros económicos de ejemplo con fuente y fecha, marcados como ejemplo/ASSUMPTION `A-DEMO-02` a `A-DEMO-06` (área DEMO, para no chocar con los ids de economics ni de field-measurement).
- Flag `DEMO_MODE=1`: la API arranca sin red ni credenciales y resuelve todo desde fixtures.
- Script de un comando que regenera fixtures desde NASA y reporta diff.
- Snapshot de la salida del motor para el lote demo por actor (test de regresión).
- Imágenes estáticas de capas GIBS del lote demo para el fallback del front.
- Checklist de pre-demo automatizado (health, fixtures, URLs, snapshot).
- Guion de demo de 4 minutos con tiempos, gancho verbal de apertura (Dune, solo verbal, sin imágenes ni logos), plan B (video grabado, ejecución local) y material para el video de YouTube.
- Guion del video parametrizado por duración: variante de 30 s (posible regla del juzgamiento global, a confirmar en las bases junto con el deck de hasta 7 slides) además de la de 4 minutos del pitch.
- Página del proyecto para NASA (`docs/demo/nasa-page.md`) y tabla `docs/demo/sources.md` con la fuente de cada número mostrado en el pitch, el video y la página.
- Entregables de transparencia referenciados: `AI_USE.md` y `PRIOR_WORK.md` en la raíz (los redacta el ingeniero principal; este change los exige en el checklist).
- Regla de comunicación: el domingo el resultado se comunica como máximo como "ganador sede"; el juzgamiento global es posterior.

## Capabilities

### New Capabilities
- `demo-mode`: operación reproducible y sin red del lote de demo (fixtures, flag, regeneración, snapshot, checklist) y materiales de presentación (guion, plan B, video).

### Modified Capabilities
- Ninguna.

## Impact

- `data/fixtures/demo/` (parquet + manifiesto + parámetros económicos de ejemplo + imágenes de capas).
- Configuración de la aplicación (pydantic-settings): `DEMO_MODE`. Afecta a `nasa-ingestion` (fuente de datos), `economics` (parámetros), `api` (`/health` informa el modo) y `web-demo` (fallback de capas).
- Scripts en `scripts/` (regeneración, pre-demo) y documentos en `docs/demo/` (guion, plan B, video).
- Sin dependencias nuevas fuera del stack declarado (httpx, earthaccess, pandas, pytest).

## Fuera de alcance

- Más de un lote cacheado (el motor sirve para cualquier punto con red; la demo offline cubre solo `demo-casilda`).
- Edición y producción final del video (se entrega guion, tomas y checklist de grabación).
- Redactar `AI_USE.md` y `PRIOR_WORK.md` (los crea el ingeniero principal).
- Imágenes, logos o marcas de Dune o de terceros: el gancho es solo verbal.
- Precios o rindes "reales" para decidir: los económicos de demo son ejemplos.
- Hosting propio de tiles GIBS (solo imágenes estáticas del lote demo).
