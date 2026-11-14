# Proposal: field-measurement

**Prioridad:** P2 (opcional; solo si el MVP P0/P1 está verde el domingo).

## Why

El desafío pide explicar en qué difiere el dato satelital de la medición de campo, y AFA quiere saber si la compactación cambia la rotación. Un "martillador" casero con el acelerómetro del celular (inspirado en el impactómetro Clegg) permite que el productor tome lecturas relativas de dureza superficial por punto del lote y verlas junto al dato SMAP L4: una forma tangible de mostrar "dato de campo vs satélite" sin pretender calibración.

## What Changes

- Se define un caso de uso y endpoint para registrar sesiones de lecturas de impacto por punto del lote (picos de desaceleración y duración del pulso por golpe, altura de caída, dispositivo).
- Se define la validación de lecturas (rangos, frecuencia de muestreo, saturación del sensor, golpes mínimos, punto dentro del lote).
- Se define una normalización relativa no calibrada dentro de una misma sesión y dispositivo (índice relativo y categoría por posición).
- Se define la procedencia: lecturas OBSERVED con dataset FIELD_HAMMER; índice DERIVED; interpretación como supuesto A-FLD-NN.
- Se definen limitaciones obligatorias en cada respuesta y una vista "dato de campo vs satélite" junto a SMAP L4.

## Capabilities

### New Capabilities
- `field-measurement`: registro, validación y normalización relativa de lecturas de impacto tomadas con el celular, con limitaciones explícitas y comparación cualitativa con SMAP L4.

### Modified Capabilities
- Ninguna en specs archivadas. Requiere agregar `FIELD_HAMMER` al conjunto de datasets de Source en `domain-models` (cambio aditivo) y dos rutas en `api`.

## Impact

- `fieldshift.application.field` (caso de uso) y rutas `POST/GET /api/v1/plots/{id}/field-readings` en el adaptador FastAPI.
- Web: pantalla de captura con DeviceMotion API (requiere HTTPS y permiso de sensores en iOS) y tarjeta "campo vs satélite".
- Almacenamiento en archivos JSON bajo `data/field/` (sin base de datos).
- Supuestos nuevos: A-FLD-01 a A-FLD-06.

## Fuera de alcance

- Calibración contra un impactómetro Clegg, penetrómetro o densidad aparente.
- Usar las lecturas en el puntaje del motor o para modificar el Suelo automáticamente.
- Comparar lecturas entre lotes, días o dispositivos distintos.
- Corregir SMAP con datos de campo o calcular correlaciones estadísticas campo-satélite.
- Mapas interpolados de compactación.
