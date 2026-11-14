# Proposal: soil-impact

**Prioridad:** P0 (el término α·ΔSuelo de la función objetivo no existe sin este índice; sin él, OWNER y COOP rankean igual que TENANT). P0 también el calendario mensual de suelo desnudo (pedido explícito del enunciado); P1 la re-ponderación de componentes por prioridades del productor.

## Why

El desafío pide explorar rotaciones que fortalezcan la salud del suelo, pero "mejora el suelo" no se puede rankear ni auditar si no es un número trazable. Necesitamos un índice ΔSuelo determinista, acotado y explicable por componentes, con cada coeficiente marcado como supuesto a validar con AFA, para que el motor pueda ponderarlo con α y la explicación pueda decir por qué una rotación suma o resta.

## What Changes

- Se define el índice ΔSuelo por rotación y por ciclo: adimensional, acotado en [-100, +100], calculado como suma ponderada de cinco componentes normalizados.
- Componentes explícitos: cobertura (días con suelo cubierto), aporte de carbono por rastrojo y biomasa (gramíneas), balance de N (leguminosas vs gramíneas), ruptura del ciclo de malezas por diversidad y efecto de raíces sobre compactación.
- Cada coeficiente es un supuesto `A-SOIL-NN` con fuente o "pendiente AFA", leído del registro `assumptions.yaml` y pasado al motor dentro de la entrada (nunca hardcodeado).
- Monotonicidad documentada y testeada: agregar un cultivo de servicio no reduce la cobertura ni los componentes de carbono, malezas y raíces.
- NDVI histórico (MODIS/HLS), como resumen mensual del lote en `EngineInput`, se usa como evidencia de cobertura observada de la rotación actual y como chequeo de consistencia del modelo, no como entrada del índice.
- Calendario mensual de días con suelo desnudo por rotación (sin cultivo vivo, y sin cultivo ni rastrojo persistente), con la fracción mensual observada de NDVI bajo umbral del lote como evidencia OBSERVED de la rotación actual.
- Los pesos w_k pueden llegar re-ponderados por las prioridades del productor (regla en actor-profiles); el índice sigue acotado y monótono.
- Salida con procedencia DERIVED, desglose por componente y por campaña, consumida por rotation-engine y explanations.

## Capabilities

### New Capabilities
- `soil-impact`: cálculo determinista del índice ΔSuelo por rotación, sus componentes, su normalización y su contraste con NDVI observado.

### Modified Capabilities
- Ninguna.

## Impact

- Módulo puro dentro de `fieldshift.engine` (sin I/O). Depende de `domain-models` (Rotación, Cultivo, Suelo, PValue) y del registro de supuestos.
- Requiere que `EngineInput` transporte los valores resueltos de los supuestos `A-SOIL-*` (cambio aditivo sobre domain-models, coordinar con su dueño).
- Consumidores: `rotation-engine` (término α·ΔSuelo, desempate y calendario en el resultado), `explanations` y `web-demo` (calendario de suelo desnudo). `nasa-ingestion` provee el resumen NDVI mensual ya resuelto.

## Fuera de alcance

- Modelos de carbono de suelo dinámicos (RothC, Century) o simulación de MO multi-año.
- Calibrar coeficientes con ensayos: los valores quedan PENDING_AFA hasta que AFA los revise.
- Usar el martillador de suelo (field-measurement) como entrada del índice; a lo sumo aparece como evidencia.
- Efecto de fertilización nitrogenada sobre el balance de N más allá del coeficiente por cultivo.
