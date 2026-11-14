# Proposal: web-demo

**Prioridad:** P0 (mapa con capas GIBS, tabla de rotaciones, selector de actor, tarjeta fija de 5 secciones con leyenda, margen en un año malo y años con pérdida, mm de lluvia sobre suelo desnudo, factibilidad "Desconocida" sin porcentajes de confianza, panel de evidencia, calendario de suelo desnudo, timeline de vulnerabilidad de helada y déficit, rango entre años secos y húmedos y simulador de chat para la demo del sábado 19:00). P1: sliders con animación de ranking, filtro por clase de año, prioridades de suelo y preferencias de presentación, lluvia sobre suelo desnudo pintada en el calendario, comparación POWER vs IMERG, robustez del ranking, tres miradas, calor y lluvia extrema en el timeline, glosario completo, fallback de tiles estáticos. P2: botón de ficha para banco o certificadora, pulido visual y modo presentación.

## Why

El jurado evalúa Pertinencia (uso central de datos NASA) y Presentación en un pitch de 4 minutos. El motor y la API no se ven: hace falta una web que muestre el lote sobre capas NASA reales, compare las rotaciones con su evidencia y deje ver en vivo cómo cambia el ranking según el actor, sin que el front invente ni calcule nada.

## What Changes

- Web de demo (single page) desplegada en Vercel que consume la API `/api/v1` (ver change `api`).
- Mapa del lote con capas NASA vía GIBS WMTS (NDVI MODIS, humedad de suelo SMAP L4, precipitación IMERG), fecha seleccionable, leyenda, resolución y limitación por capa, y fallback a imagen estática cacheada para el lote demo.
- Tabla comparativa de al menos 3 rotaciones (actual destacada) con puntaje y desglose (VAN, α·ΔSuelo, λ·Riesgo), diferencia contra la actual (`score_delta_vs_current`), factibilidad hídrica (incluida "Desconocida"), ΔSuelo, riesgo, margen en un año malo, años con pérdida y lluvia sobre suelo desnudo.
- Tarjeta fija de 5 secciones por rotación que cierra con la leyenda, agrupable en tres miradas (clima, suelo y agua, economía), con robustez y comparación de lluvia POWER vs IMERG cuando la API las envía.
- Calendario mensual de suelo desnudo por rotación con el NDVI histórico del lote como evidencia observada, timeline mensual de vulnerabilidad por cultivo y rango de margen y de agua entre años secos y húmedos, todo tal como lo envía la API.
- Filtro por clase de año (todos, solo secos, solo húmedos), controles de prioridades de suelo y preferencias de presentación (primero las no riesgosas en agua, primero las de doble cultivo) que piden una nueva evaluación a la API y muestran el orden que ella devuelve (P1).
- Selector de actor (OWNER, TENANT, COOP, BANK) y sliders H, α, λ que recalculan contra la API y muestran cambios de posición en el ranking.
- Panel de evidencia y procedencia: badge OBSERVED/DERIVED/ASSUMPTION/USER_INPUT por número, tooltip con dataset, variable, período, resolución o assumption_id; lista de faltantes y riesgos.
- Glosario en lenguaje simple (desde `GET /glossary`).
- Simulador de chat estilo WhatsApp embebido contra `POST /chat/simulate`.
- Leyendas fijas "Apoya, no reemplaza al agrónomo" y "Escenarios históricos, no predicción".
- Responsive (proyector y celular) y accesibilidad básica; tests E2E con Playwright contra API mockeada y contra API en DEMO_MODE.

## Capabilities

### New Capabilities
- `web-demo`: interfaz web de presentación del análisis de rotaciones (mapa NASA, ranking por actor, evidencia y procedencia, glosario, simulador de chat), solo de presentación.

### Modified Capabilities
- Ninguna.

## Impact

- Nuevo directorio `web/` (Vite + React + TypeScript + Leaflet), independiente del paquete Python.
- Depende de los endpoints de `api` (`/evaluate`, `/sensitivity`, `/rotations/catalog`, `/actors/profiles`, `/plots/{id}/context`, `/glossary`, `/assumptions`, `/chat/simulate`, `/health`) y de los modelos de `domain-models` (vía JSON Schema exportado).
- Depende de `demo-mode` para fixtures del lote `demo-casilda` y de las imágenes estáticas de capas.
- Dependencias OSS: react, react-dom, leaflet, react-leaflet, vite, typescript, @playwright/test, vitest. Declaradas en README.

## Fuera de alcance

- Cualquier cálculo del motor en el navegador (puntajes, ranking, factibilidad, riesgo) y cualquier reordenamiento propio.
- Porcentajes de confianza o probabilidades en la UI.
- Login, multi-usuario, persistencia de lotes o dibujo de polígonos.
- Capas GRACE-FO en el mapa si GIBS no las publica como WMTS: se muestran como dato regional en el panel de evidencia.
- "Máquina del tiempo" animada y martillador de suelo (otros changes, opcionales).
- Internacionalización: la UI es solo en español.
