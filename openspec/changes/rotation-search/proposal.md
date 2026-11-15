# Proposal: rotation-search

**Prioridad:** P1 (se implementa el 15/11; no cambia el ranking del catálogo que ya muestra la demo).

## Why

Hoy el motor elige la mejor rotación entre 5 armadas a mano (el catálogo) más la actual. Eso cumple el pedido del desafío (al menos 3 estrategias, incluida la actual), pero no permite afirmar que la recomendada sea la mejor posible. Con el catálogo de cultivos y las reglas de campaña que ya tiene el dominio, el espacio de rotaciones razonables de 1 a 3 campañas es chico (unas 300 a 400 tras deduplicar), así que se puede evaluar entero: búsqueda exhaustiva, sin heurísticas, con el mismo motor determinista.

## What Changes

- Generador determinista de campañas válidas y de rotaciones de 1 a 3 campañas, deduplicadas por equivalencia cíclica y por periodicidad (una rotación de 2 campañas iguales es la misma que la de 1).
- Reglas agronómicas de poda registradas como supuestos con id (pendientes de AFA): el doble cultivo de verano solo después de trigo; un servicio solo antes de un cultivo de verano de primera; cada ciclo incluye al menos una gramínea (maíz, trigo o servicio de gramínea); ningún cultivo de verano más de dos campañas seguidas. El catálogo y la rotación actual se evalúan siempre, aunque no cumplan las reglas.
- Búsqueda exhaustiva por actor y filtro de clase de año: se evalúan todas las candidatas con el motor (`evaluate`) y se guardan el ranking completo de elegibles, el frente de Pareto en (margen esperado, ΔSuelo, riesgo) y la comparación contra la mejor del catálogo.
- Precálculo: la búsqueda tarda decenas de segundos por actor, demasiado para cada pedido. Un script la corre para los cuatro perfiles predefinidos y los cuatro filtros de año y guarda el resultado como fixture con `input_hash`, `engine_version` y versión del generador; la tarea diaria lo regenera junto con los datos NASA.
- API `GET /api/v1/rotations/search?actor=&year_class_filter=` que sirve el precálculo; nunca evalúa en el pedido.
- Web: sección "¿Hay algo mejor fuera de estas 5?" bajo el ranking, con las mejores rotaciones encontradas, si superan a la mejor del catálogo y si están en el frente de Pareto.

## Capabilities

### New Capabilities
- `rotation-search`: generación de candidatas, poda por reglas agronómicas, búsqueda exhaustiva precalculada y frente de Pareto.

### Modified Capabilities
- Ninguna. El motor (`rotation-engine`) se usa sin cambios: la búsqueda solo le pasa más candidatas.

## Impact

- Nuevo módulo `rastrojo.application.search` (generador, reglas, búsqueda, Pareto) y script `scripts/precompute_search.py`.
- Nuevos supuestos A-AGR-02 a A-AGR-05 en `data/assumptions.yaml`.
- Fixture `data/fixtures/demo/search/`, incluido en el deploy de Vercel y en el workflow diario.
- Los sliders y el arriendo editable no aplican a la búsqueda: usa los perfiles predefinidos. La web lo dice.
