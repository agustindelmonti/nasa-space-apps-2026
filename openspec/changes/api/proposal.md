# Proposal: api

**Prioridad:** P0 (POST /evaluate lite y completo, catálogo, perfiles, health, errores tipados, CORS para la demo del sábado); P1 (contexto del lote, glosario, supuestos, rate limit, OpenAPI pulido, POST /sensitivity, filtro por clase de año, suelo desde caché SoilGrids en la resolución lite, preferencias de presentación y robustez del ranking); P2 (métricas de latencia, rutas de lecturas de campo, POST /rotation-sheet con la ficha para banco o certificadora).

## Why

El motor es puro y no hace I/O; la web de demo y el canal WhatsApp necesitan un único punto HTTP que resuelva la entrada (desde caché o fixtures), corra el motor y devuelva resultado y explicación con contratos estables. Sin un contrato fijo y errores tipados, front, simulador y webhook se rompen entre sí durante el hackathon.

## What Changes

- Se publica una API FastAPI bajo `/api/v1` con los endpoints transversales: POST /evaluate, POST /sensitivity (P1, de actor-profiles), GET /rotations/catalog, GET /actors/profiles, GET /plots/{plot_id}/context, GET /glossary, GET /assumptions, POST /whatsapp/webhook, POST /chat/simulate, GET /health, POST /rotation-sheet (P2, ficha de explanations) y POST/GET /plots/{plot_id}/field-readings (P2, de field-measurement).
- Se agrega un filtro opcional por clase de año (ALL, DRY, NORMAL, WET) en /evaluate y /sensitivity que el motor aplica re-ponderando escenarios y declara en la salida.
- Se define un request "lite" (lat/lon + rotación actual + actor) que la capa de aplicación resuelve contra caché y fixtures, además del request completo con `EngineInput`. El suelo se resuelve con prioridad dato del usuario > caché SoilGrids > A-WAT-14 genérico, registrando un faltante en los dos últimos casos.
- Se agregan `display_preferences` (WATER_SAFE_FIRST, DOUBLE_CROP_FIRST) que la aplicación convierte en `display_order` sin tocar el motor ni el `input_hash`, y `include_robustness` para el indicador de actor-profiles.
- Se agrega `POST /rotation-sheet` (P2): mismo request que /evaluate más `rotation_id`, responde la ficha exportable de explanations. Es POST porque necesita la entrada completa del lote y la API no persiste evaluaciones.
- Se define un formato de error único `{code, message, details}` con catálogo cerrado de códigos y su estado HTTP.
- Se garantiza idempotencia de POST /evaluate: misma entrada, misma respuesta byte a byte, con header `X-Input-Hash`.
- Se agregan CORS para el front, límites de tamaño, timeouts, rate limit básico para endpoints públicos de chat, OpenAPI publicado y health con versión del motor y estado de caché.

## Capabilities

### New Capabilities
- `api`: contrato HTTP versionado, resolución de request lite, errores tipados, idempotencia, CORS, límites y health.

### Modified Capabilities
- Ninguna.

## Impact

- Adaptador `fieldshift.adapters.api` (FastAPI) y casos de uso en `fieldshift.application`.
- Depende de `domain-models`, `rotation-engine`, `explanations`, `nasa-ingestion` (caché), `actor-profiles` (perfiles y sensibilidad), `economics` (parámetros con fuente y fecha), `field-measurement` (P2) y `demo-mode` (fixtures, DEMO_MODE=1). El comportamiento conversacional de /whatsapp/webhook y /chat/simulate se especifica en `whatsapp-channel`.
- Consumidores: `web-demo` y simulador de chat. Deploy en Render o Fly (gratuito).
- Dependencias: `fastapi`, `uvicorn`, `pydantic-settings`.

## Fuera de alcance

- Autenticación de usuarios, multi-tenant y persistencia (no hay base de datos).
- Ingesta en línea desde la API: la API solo lee caché y fixtures; refrescar la caché es un comando de `nasa-ingestion`.
- Versionado v2 y compatibilidad hacia atrás entre releases.
- Rate limit distribuido (solo en memoria, una instancia).
