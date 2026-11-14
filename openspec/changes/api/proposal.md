# Proposal: api

**Prioridad:** P0 (POST /evaluate lite y completo, catálogo, perfiles, health, errores tipados, CORS para la demo del sábado); P1 (contexto del lote, glosario, supuestos, rate limit, OpenAPI pulido); P2 (métricas de latencia).

## Why

El motor es puro y no hace I/O; la web de demo y el canal WhatsApp necesitan un único punto HTTP que resuelva la entrada (desde caché o fixtures), corra el motor y devuelva resultado y explicación con contratos estables. Sin un contrato fijo y errores tipados, front, simulador y webhook se rompen entre sí durante el hackathon.

## What Changes

- Se publica una API FastAPI bajo `/api/v1` con los endpoints transversales: POST /evaluate, GET /rotations/catalog, GET /actors/profiles, GET /plots/{plot_id}/context, GET /glossary, GET /assumptions, POST /whatsapp/webhook, POST /chat/simulate y GET /health.
- Se define un request "lite" (lat/lon + rotación actual + actor) que la capa de aplicación resuelve contra caché y fixtures, además del request completo con `EngineInput`.
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
- Depende de `domain-models`, `rotation-engine`, `explanations`, `nasa-ingestion` (caché), `actor-profiles`, `economics` (parámetros con fuente y fecha) y `demo-mode` (fixtures, DEMO_MODE=1). El comportamiento conversacional de /whatsapp/webhook y /chat/simulate se especifica en `whatsapp-channel`.
- Consumidores: `web-demo` y simulador de chat. Deploy en Render o Fly (gratuito).
- Dependencias: `fastapi`, `uvicorn`, `pydantic-settings`.

## Fuera de alcance

- Autenticación de usuarios, multi-tenant y persistencia (no hay base de datos).
- Ingesta en línea desde la API: la API solo lee caché y fixtures; refrescar la caché es un comando de `nasa-ingestion`.
- Versionado v2 y compatibilidad hacia atrás entre releases.
- Rate limit distribuido (solo en memoria, una instancia).
