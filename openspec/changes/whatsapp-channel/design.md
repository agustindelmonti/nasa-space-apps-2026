# Design: whatsapp-channel

## Context

Ver proposal.md. El contrato HTTP común (formato de error, límites de tamaño, rate limit, CORS) lo define `api`. Los textos (resumen, detalle, glosario, leyendas, partición a 1600 caracteres) los produce `explanations`. Este change define el flujo conversacional, el adaptador Twilio, el simulador y la capa LLM opcional.

## Goals / Non-Goals

**Goals:** flujo de menús testeable sin red ni Twilio; un solo motor conversacional para WhatsApp y simulador; demo en vivo robusta aunque Twilio o el LLM fallen; cero datos personales en logs.

**Non-Goals:** NLU o lenguaje libre, multi-idioma, persistencia de sesiones, WhatsApp Business productivo.

## Decisions

1. **Motor conversacional puro** en `fieldshift.application.conversation`: `step(session, inbound, deps) -> (session', outbound, effects)`. La evaluación se inyecta como puerto (`Evaluator`), y el reloj como `Clock` para TTL; así los tests son deterministas. Estados y transiciones en una tabla declarativa (dict estado → handler). Alternativa descartada: librería de FSM (`transitions`): dependencia extra para 7 estados.
2. **Modelo `Session`** (Pydantic, frozen): `user_key`, `state`, `location?`, `current_rotation_id?`, `actor?`, `last_result_ref?`, `invalid_location_attempts`, `last_seen`. Cada paso devuelve una sesión nueva (sin mutación).
3. **`SessionStore` en memoria** (dict + orden LRU) con TTL y tope de sesiones configurables, lock por clave para requests concurrentes del mismo usuario, y set de `MessageSid` vistos con el mismo TTL. Clave = `wa:<hash>` o `sim:<session_id>`. Alternativa descartada: Redis (otro servicio a deployar sin necesidad para la demo).
4. **Interfaz de canal**: `InboundMessage{user_key, kind: TEXT|LOCATION|MEDIA, text?, lat?, lon?, message_id?}` y `OutboundMessage{text}`. `TwilioAdapter` parsea el form (`From`, `Body`, `Latitude`, `Longitude`, `NumMedia`, `MessageSid`) y renderiza TwiML con un `<Message>` por saliente; `SimulatorAdapter` usa JSON. Alternativa descartada: llamar a la API REST de Twilio para enviar (requiere credenciales salientes y reintentos; responder TwiML en el mismo request alcanza).
5. **Firma**: validación HMAC-SHA1 de Twilio sobre `PUBLIC_WEBHOOK_URL` configurada + parámetros del form, comparación en tiempo constante. Se usa el validador del SDK oficial de Twilio si está disponible; si no, implementación propia de ~20 líneas con test de vectores conocidos.
6. **Parseo de coordenadas**: regex cerradas para tres formatos (`-33.04,-61.17`, `-33.04 -61.17`, `-33,04; -61,17`); cualquier otra cosa es inválida (no se adivina). Validación de rango con el bbox de `domain-models`.
7. **Lote de demo**: "DEMO" mapea a la ubicación del lote `demo-casilda` de `demo-mode`.
8. **Evaluación desde el chat**: el `Evaluator` arma un request lite (lat/lon, rotación, actor) y llama al mismo caso de uso que POST /evaluate, pidiendo formato `whatsapp`; los errores OUT_OF_COVERAGE y DATA_UNAVAILABLE se traducen a frases fijas.
9. **Capa LLM opcional** (`fieldshift.adapters.whatsapp.rephrase`): `Rephraser` con implementación nula por defecto y una implementación HTTP para el proveedor elegido, activa solo con `LLM_REPHRASE_ENABLED=true` y clave. Pipeline: plantilla → LLM (timeout) → guardas → texto final o plantilla. Guardas: (a) `numbers(out) ⊆ numbers(in)` con `parse_ar_numbers` de `explanations`; (b) `crops(out) ⊆ crops(in)` con léxico de nombres de cultivos y rotaciones del catálogo (con sinónimos comunes, por ejemplo "poroto" para soja, y cultivos fuera de catálogo como "girasol" o "sorgo" que siempre violan); (c) sin expresiones prohibidas; (d) leyendas y marcas de supuestos presentes literalmente; (e) largo dentro del límite. Las leyendas y la nota de supuestos se separan antes de reformular y se reanexan después. Alternativa descartada: pedir al LLM que "no invente números" solo con instrucciones (no verificable).
10. **Logging**: `user_hash = sha256(salt + phone)[:16]` con `PHONE_HASH_SALT` del entorno; eventos estructurados `{user_hash, state_from, state_to, event_kind, coverage, llm_fallback_reason?}`. Coordenadas nunca se loguean. Filtro de logging que redacta valores de secretos por si se cuelan.
11. **Variables de entorno**: `TWILIO_AUTH_TOKEN`, `TWILIO_ACCOUNT_SID`, `PUBLIC_WEBHOOK_URL`, `PHONE_HASH_SALT`, `SESSION_TTL_MINUTES`, `SESSION_MAX`, `LLM_REPHRASE_ENABLED`, `LLM_API_KEY`, `LLM_TIMEOUT_S`; todas en `.env.example` sin valores.
12. **Tarjeta del detalle**: se reusa tal cual la tarjeta WhatsApp de explanations (rótulos fijos y leyenda de cierre); el particionador garantiza que la leyenda quede en el último mensaje de la tarjeta. El chat no arma textos propios con números.
13. **Ordenar la lista (P1)**: la sesión guarda `display_preferences`; el `Evaluator` las pasa a la api y el resumen se rearma con el `display_order` devuelto. Alternativa descartada: reordenar en el motor conversacional (duplica la regla de la api).

## Risks / Trade-offs

- [Twilio Sandbox exige que cada teléfono se una con un código y expira a las 72 h] → el simulador web es el camino principal de la demo; se re-une el teléfono del presentador el domingo temprano.
- [Webhook tarda más de lo que Twilio espera por cold start] → DEMO_MODE con fixtures y ping a /health antes del pitch; en error se responde disculpa con opción de reiniciar.
- [Sesiones se pierden al reiniciar el servidor] → aceptado: el usuario recibe el saludo y vuelve a empezar en 4 mensajes.
- [Guardas del LLM rechazan reformulaciones válidas] → se prefiere fallback seguro; se loguea el motivo para ajustar el léxico.
- [Salida no determinista con LLM activo] → el flag está apagado por defecto y los tests de determinismo corren con el flag apagado.

## Open Questions

- Proveedor LLM a usar si se habilita la capa P2 (no cambia la interfaz `Rephraser`).
- Texto exacto del saludo y frases fijas: lo redacta el equipo en rioplatense.
