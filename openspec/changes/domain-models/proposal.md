# Proposal: domain-models

**Prioridad:** P0 (bloquea a todas las demás capabilities).

## Why

Todas las capas (ingesta, motor, explicaciones, API, canales) tienen que hablar el mismo idioma. Si el vocabulario de dominio no está fijado antes de codear, cada módulo inventa su propio "lote" o "rotación" y el determinismo y la procedencia se rompen en los bordes. Este change define el contrato de datos compartido, validado con Pydantic v2, con procedencia obligatoria en cada número.

## What Changes

- Se define el vocabulario de dominio: Lote, Suelo, Cultivo, Rotación, Perfil de actor, Parámetros económicos, Escenario climático, Evaluación/Recomendación, Evidencia, Faltante, Riesgo y Procedencia.
- Se define un tipo de valor con procedencia (`valor + unidad + procedencia`) que usan todos los números que cruzan capas.
- Se define el sobre de entrada y salida del motor (`EngineInput`, `EngineOutput`) con hash SHA-256 de la entrada canónica y versión del motor.
- Se define la serialización JSON canónica (claves ordenadas, redondeo declarado) que habilita comparar salidas byte a byte.
- Se fija un catálogo cerrado de cultivos para el MVP, con calendario único de siembra y cosecha (A-AGR-01).
- Se fija la regla de procedencia: productos de modelos externos (SMAP L4, POWER/MERRA-2, SoilGrids, GLDAS, GRACE-FO) son OBSERVED con `is_modeled=true`; DERIVED es solo lo que calcula el sistema.
- Agregados acordados en la reconciliación: datasets FIELD_HAMMER, SRTM, ECOSTRESS y GLDAS; área DEMO en ids de supuestos; insumos hídricos y supuestos resueltos en `EngineInput`; clase anual y por estación en el escenario; resultado con elegibilidad, ajustes hídricos, diferencia contra la actual, rango de margen por clase y calendarios mensuales; parámetros económicos con base de precio, modo de cosecha, flete y arrendamiento; perfil con capital opcional, prioridades de suelo (sin agua ni ingreso suplementario) y ventanas de maquinaria; factibilidad con estado UNKNOWN; resultado con años con pérdida, margen del peor año y lluvia sobre suelo desnudo; filtro por clase de año con NORMAL; `input_hash` independiente del orden de listas.

## Capabilities

### New Capabilities
- `domain-models`: modelos de dominio validados, procedencia, catálogo de cultivos, sobres de entrada/salida del motor y serialización canónica.

### Modified Capabilities
- Ninguna (repo nuevo).

## Impact

- Paquete Python `fieldshift.domain` (nombre tentativo) del que dependen `engine`, `data`, `application` y `adapters`.
- Esquemas JSON exportados desde Pydantic que consumen el front y el simulador de WhatsApp.
- Dependencias: `pydantic>=2`, `pydantic-settings`.

## Fuera de alcance

- Persistencia (no hay base de datos en el MVP; todo es caché en archivos y fixtures).
- Multi-lote, multi-usuario y autenticación.
- Valores por defecto agronómicos o económicos: los define cada capability como ASSUMPTION con fuente.
