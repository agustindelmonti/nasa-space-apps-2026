# Proposal: explanations

**Prioridad:** P0 (explicación por rotación y formato WhatsApp para la demo del sábado); P1 (resumen propietario vs arrendatario, glosario completo); P2 (pulido de redacción).

## Why

El desafío pide, para cada rotación, por qué, con qué evidencia, beneficios, qué falta y qué riesgos, en lenguaje simple. Un ranking con números sueltos no le sirve a un productor ni a un agrónomo de AFA, y un texto libre generado por un LLM puede inventar cifras. Necesitamos explicaciones generadas por plantillas deterministas, donde cada número citado sea trazable a la salida del motor con su procedencia.

## What Changes

- Se agrega un generador de explicaciones puro (sin LLM, red ni reloj) que toma la salida del motor (`EngineOutput`) y su entrada resuelta y produce, por rotación: por qué (posición y términos dominantes del puntaje), evidencia, beneficios, faltantes y riesgos.
- Se agrega un resumen comparativo y una sección "qué cambia si sos propietario vs arrendatario" a partir de dos evaluaciones del mismo lote.
- Se define la regla de trazabilidad: todo número del texto existe en la salida del motor (o en su entrada resuelta con el mismo `input_hash`) y se lista como cita con su procedencia. Un test extrae los números del texto y los busca.
- Se define un glosario en lenguaje simple (evapotranspiración, NDVI, anomalía de humedad, balance hídrico, heladas, GRACE-FO y agua subterránea, dato satelital vs medición de campo).
- Se fijan leyendas obligatorias ("apoya, no reemplaza al agrónomo", "escenarios históricos, no predicción") y el marcado visible de supuestos.
- Se definen tres formatos: estructurado (JSON), texto largo web y texto corto WhatsApp con partición determinista por límite de caracteres.
- Se fija el formato numérico argentino (coma decimal, punto de miles) y el registro de español rioplatense.

## Capabilities

### New Capabilities
- `explanations`: generación determinista de explicaciones por rotación, resumen comparativo, glosario, leyendas, formatos de salida y trazabilidad de números.

### Modified Capabilities
- Ninguna.

## Impact

- Módulo puro en la capa de aplicación (`fieldshift.application.explanations`, tentativo), consumido por `api` (POST /evaluate, GET /glossary) y `whatsapp-channel`.
- Depende de `domain-models` (Evidencia, Faltante, Riesgo, PValue, Provenance) y de la salida de `rotation-engine`; usa el catálogo de datasets de `nasa-ingestion` para resoluciones y limitaciones, y los nombres de perfiles de `actor-profiles`.
- Snapshot tests de textos en `quality`.
- Sin dependencias nuevas.

## Fuera de alcance

- Reformulación con LLM (vive en `whatsapp-channel`, apagada por defecto, y usa las guardas definidas allí).
- Otros idiomas distintos del español rioplatense.
- Cálculos nuevos: el generador no computa números que el motor no haya producido.
- Gráficos y visualizaciones (los hace `web-demo`).
