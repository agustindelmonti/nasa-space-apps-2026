# Proposal: field-measurement

**Prioridad:** P2 (opcional; solo si el MVP P0/P1 está verde el domingo).

## Why

El desafío pide explicar en qué difiere el dato satelital de la medición de campo, y AFA quiere saber si la compactación cambia la rotación. Un "martillador" casero con el acelerómetro del celular (inspirado en el impactómetro Clegg) permite que el productor tome lecturas relativas de dureza superficial por punto del lote y verlas junto al dato SMAP L4: una forma tangible de mostrar "dato de campo vs satélite" sin pretender calibración.

## What Changes

- Se fija el accesorio del martillador v0 según el master doc: masa de ~2 kg en un carro sobre riel o tubo guía, alturas de 150, 300 y 450 mm, y v0 usa 150 mm porque el acelerómetro del celular satura en alturas mayores (A-FLD-02, corrige el valor previo de 30 cm).
- Se define un caso de uso y endpoint para registrar sesiones de lecturas de impacto por punto del lote (picos de desaceleración y duración del pulso por golpe, masa y altura de caída en mm, dispositivo).
- Se define un escenario de demo: una caja de tierra suelta y una compactada producen índices relativos distintos y ordenados (compactada mayor).
- Se define la validación de lecturas (rangos, frecuencia de muestreo, saturación del sensor, golpes mínimos, punto dentro del lote).
- Se define una normalización relativa no calibrada dentro de una misma sesión y dispositivo (índice relativo y categoría por posición).
- Se define la procedencia: lecturas OBSERVED con dataset FIELD_HAMMER; índice DERIVED; interpretación como supuesto A-FLD-NN.
- Se definen limitaciones obligatorias en cada respuesta y una vista "dato de campo vs satélite" junto a SMAP L4.

## Capabilities

### New Capabilities
- `field-measurement`: registro, validación y normalización relativa de lecturas de impacto tomadas con el celular, con limitaciones explícitas y comparación cualitativa con SMAP L4.

### Modified Capabilities
- Ninguna en specs archivadas. Usa `FIELD_HAMMER`, ya agregado al enum de datasets de Source en `domain-models`, y las rutas POST/GET de lecturas de campo ya listadas en `api` (P2).

## Impact

- `fieldshift.application.field` (caso de uso) y rutas `POST/GET /api/v1/plots/{id}/field-readings` en el adaptador FastAPI.
- Web: pantalla de captura con DeviceMotion API (requiere HTTPS y permiso de sensores en iOS) y tarjeta "campo vs satélite".
- Almacenamiento en archivos JSON bajo `data/field/` (sin base de datos).
- Supuestos nuevos: A-FLD-01 a A-FLD-06 (el área FLD es exclusiva de este change; el lote demo usa A-DEMO-01).

## Fuera de alcance

- Calibración contra un impactómetro Clegg, penetrómetro o densidad aparente.
- Versión v1 con ESP32 y acelerómetro ADXL375 (±200 g) calibrada contra penetrómetro: queda como trabajo futuro documentado.
- Usar las lecturas en el puntaje del motor o para modificar el Suelo automáticamente.
- Comparar lecturas entre lotes, días o dispositivos distintos.
- Corregir SMAP con datos de campo o calcular correlaciones estadísticas campo-satélite.
- Mapas interpolados de compactación.
