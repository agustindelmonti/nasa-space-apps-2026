# Proposal: rotation-engine

**Prioridad:** P0 (es el corazón de la demo del sábado: sin ranking no hay nada que mostrar). P1: filtro por clase de año (incluido NORMAL para la robustez), ventanas de maquinaria y pesos de prioridades del productor sobre ΔSuelo.

## Why

El desafío pide comparar al menos 3 rotaciones, incluida la actual, según las prioridades de cada actor, y explicar por qué. Hace falta un motor puro y determinista que junte economía, suelo, agua y clima en un puntaje con desglose, que respete las restricciones del actor sin esconder opciones y que produzca la misma salida byte a byte para la misma entrada.

## What Changes

- Generación de candidatas desde el catálogo cerrado (R_SOY_MONO, R_MAIZE_SOY, R_WHEAT_SOY2_MAIZE, R_MAIZE_SOY_COVER, R_SOY_COVER) más la rotación actual, con deduplicación por equivalencia cíclica.
- Filtrado por restricciones del actor (doble cultivo, cultivo de servicio, capital de trabajo y, en P1, ventanas de maquinaria) y por datos faltantes, con motivo codificado por cada descarte; las descartadas se devuelven marcadas, no se esconden.
- Evaluación por escenario climático histórico con el estado hídrico que calcula water-feasibility como submódulo del motor (no se precalcula afuera): NOT_FEASIBLE significa "no se siembra ese año" y RISKY significa "rinde de año seco"; exclusión solo si un cultivo nunca es factible. UNKNOWN (datos insuficientes) nunca excluye: la rotación sigue elegible, sin ajuste en los escenarios sin dato, con Faltante, y se ordena como RISKY en la presentación.
- E[Margen] ponderado, Riesgo como expected shortfall de cola q del margen anual por posición, escalado por el factor de anualidad; puntaje exactamente `VAN + α·ΔSuelo − λ·Riesgo`. Las prioridades del productor solo re-ponderan los w_k de ΔSuelo (P1); no hay términos agregados.
- Salida por rotación con `score_delta_vs_current`, rango de margen por clase anual (mínimo, esperado, máximo), años con pérdida y margen del peor año (economics, P0), lluvia sobre suelo desnudo (soil-impact, P0), calendario de suelo desnudo y calendario de vulnerabilidad (water-feasibility).
- Filtro opcional por clase de año (todos, solo DRY, solo NORMAL, solo WET) que re-pondera escenarios de forma determinista y se declara en la salida (P1); lo usa también el indicador de robustez de actor-profiles.
- Ranking estable con los desempates de xcut.md; siempre al menos 3 opciones incluida la actual.
- Salida `EngineOutput` con `input_hash` y `engine_version`; sin I/O, reloj, random ni LLM.

## Capabilities

### New Capabilities
- `rotation-engine`: generación, filtrado, evaluación, puntaje y ranking determinista de rotaciones por actor.

### Modified Capabilities
- Ninguna.

## Impact

- `rastrojo.engine` (función pública única `evaluate(EngineInput) -> EngineOutput`). Usa `economics`, `soil-impact`, el estado hídrico de `water-feasibility` y los escenarios de `climate-scenarios`.
- Consumidores: `application` (casos de uso), `api` (POST /api/v1/evaluate), `explanations`, `actor-profiles` (sensibilidad), `quality` (tests de determinismo y propiedades).
- Usa los agregados acordados en domain-models: resultado con `eligible`, `exclusion_reasons`, `water_adjustments`, `score_delta_vs_current`, rango de margen y calendarios; `EngineInput` con supuestos resueltos, insumos hídricos y filtro por clase de año.

## Fuera de alcance

- Optimización combinatoria sobre rotaciones arbitrarias: solo catálogo cerrado + actual.
- Contratista como perfil propio con su calendario de servicios (P2 futuro); las ventanas de maquinaria del productor sí entran como restricción (P1).
- Monte Carlo, pronósticos o generación sintética de años.
- Reformulación en lenguaje natural (es de explanations / whatsapp-channel).
