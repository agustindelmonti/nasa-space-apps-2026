# Proposal: explanations

**Prioridad:** P0 (tarjeta fija de 5 secciones con leyenda por rotación, incertidumbre entre años secos y húmedos, años con pérdida y margen en un año malo, lluvia sobre suelo desnudo, factibilidad "desconocida" en vez de "no apta", lista de expresiones prohibidas, calendarios de suelo desnudo y de vulnerabilidad de helada y déficit, formato WhatsApp para la demo del sábado); P1 (tres miradas deterministas, robustez del ranking, comparación de lluvia POWER vs IMERG, resumen propietario vs arrendatario, glosario completo, calor y lluvia extrema); P2 (ficha exportable para banco o certificadora, pulido de redacción).

## Why

El desafío pide, para cada rotación, por qué, con qué evidencia, beneficios, qué falta y qué riesgos, en lenguaje simple. Un ranking con números sueltos no le sirve a un productor ni a un agrónomo de AFA, y un texto libre generado por un LLM puede inventar cifras. Necesitamos explicaciones generadas por plantillas deterministas, donde cada número citado sea trazable a la salida del motor con su procedencia.

## What Changes

- Se agrega un generador de explicaciones puro (sin LLM, red ni reloj) que toma la salida del motor (`EngineOutput`) y su entrada resuelta y produce, por rotación, una tarjeta fija de 5 secciones (por qué, evidencia, beneficios frente a la actual, faltantes, riesgos) que siempre cierra con la leyenda "apoya, no reemplaza al agrónomo".
- Se explican "margen en un año malo" y "en cuántos de los N años reales habrías perdido plata", y los mm de lluvia caídos sobre suelo desnudo, citados desde el motor.
- Se agrupa la explicación en tres miradas deterministas (clima, suelo y agua, economía) como secciones de plantilla, sin LLM (P1).
- Se agrega una ficha exportable por rotación para banco o certificadora con riesgo, factibilidad hídrica y beneficio de suelo, todo con procedencia (P2), servida por `api`.
- Nunca se muestra un "% de confianza": si falta un dato la factibilidad se dice "desconocida", no "no apta".
- Se agrega un resumen comparativo, con la diferencia contra la rotación actual tomada de `score_delta_vs_current` del motor, y una sección "qué cambia si sos propietario vs arrendatario" a partir de dos evaluaciones del mismo lote.
- Se explica la incertidumbre con el rango entre años secos y húmedos del margen y del balance hídrico (mínimo, esperado, máximo por clase), no solo el valor esperado, y el Riesgo como lo que se pierde en los peores años (cola de peso q de los márgenes, A-ACT-05).
- Se explican el calendario de suelo desnudo (con el NDVI histórico del lote como evidencia observada) y el calendario de vulnerabilidad por cultivo.
- Se define la regla de trazabilidad: todo número del texto existe en la salida del motor (o en su entrada resuelta con el mismo `input_hash`) y se lista como cita con su procedencia. Un test extrae los números del texto y los busca.
- Se define un glosario en lenguaje simple (evapotranspiración, NDVI, anomalía de humedad, balance hídrico, heladas, estrés térmico, GRACE-FO y agua subterránea, dato satelital vs medición de campo y cómo combinarlos mejora la precisión).
- Se fijan leyendas obligatorias ("apoya, no reemplaza al agrónomo", "escenarios históricos, no predicción") y el marcado visible de supuestos.
- Se definen tres formatos: estructurado (JSON), texto largo web y texto corto WhatsApp con partición determinista por límite de caracteres.
- Se fija el formato numérico argentino (coma decimal, punto de miles) y el registro de español rioplatense.

## Capabilities

### New Capabilities
- `explanations`: generación determinista de explicaciones por rotación, resumen comparativo, glosario, leyendas, formatos de salida y trazabilidad de números.

### Modified Capabilities
- Ninguna.

## Impact

- Módulo puro en la capa de aplicación (`fieldshift.application.explanations`, tentativo), consumido por `api` (POST /evaluate, POST /rotation-sheet, GET /glossary), `web-demo` y `whatsapp-channel`.
- Depende de `domain-models` (Evidencia, Faltante, Riesgo, PValue, Provenance) y de la salida de `rotation-engine`; usa el catálogo de datasets de `nasa-ingestion` para resoluciones y limitaciones, y los nombres de perfiles de `actor-profiles`.
- Snapshot tests de textos en `quality`.
- Sin dependencias nuevas.

## Fuera de alcance

- Reformulación con LLM (vive en `whatsapp-channel`, apagada por defecto, y usa las guardas definidas allí).
- Otros idiomas distintos del español rioplatense.
- Cálculos nuevos: el generador no computa números que el motor no haya producido.
- Gráficos y visualizaciones (los hace `web-demo`).
- PDF de la ficha: se entrega JSON y texto con marcado mínimo; imprimir o exportar a PDF lo hace el navegador.
