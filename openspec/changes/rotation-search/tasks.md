# Tasks: rotation-search

## 1. Generador y reglas

- [x] 1.1 Supuestos A-AGR-02 a A-AGR-05 en `data/assumptions.yaml` y `docs/assumptions.md`
- [x] 1.2 `rastrojo.application.search`: campañas válidas, rotaciones canónicas de 1 a 3, ids `G_` estables y nombres generados; tests "Doble cultivo solo después de trigo", "Servicio antes de un cultivo de primera", "Ciclo equivalente" y "Secuencia periódica"
- [x] 1.3 Reglas de ciclo con conteo de descartes por regla; catálogo y actual siempre incluidos; test "Soja continua"

## 2. Búsqueda

- [x] 2.1 Búsqueda con una sola llamada a `evaluate`, ranking de elegibles, Pareto y comparación con el catálogo; tests "La mejor encontrada no puede ser peor que la del catálogo", "Frente de Pareto" y determinismo
- [x] 2.2 `scripts/precompute_search.py` para 4 actores × 4 filtros; fixture en `data/fixtures/demo/search/`

## 3. Entrega

- [x] 3.1 `GET /api/v1/rotations/search` con `SEARCH_NOT_PRECOMPUTED`; test "Pedido a la API"
- [x] 3.2 Web: sección "¿Hay algo mejor fuera de estas 5?" con nota de perfil predefinido; vitest y Playwright en verde
- [x] 3.3 Vercel `includeFiles` y workflow diario con el precálculo
