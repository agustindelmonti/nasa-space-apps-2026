# Proposal: whatsapp-channel

**Prioridad:** P0 (máquina de estados, simulador web vía POST /chat/simulate, adaptador Twilio Sandbox con firma, detalle como tarjeta fija de 5 secciones con leyenda); P1 (TTL de sesión, glosario, cambio de actor y orden de presentación en el chat, logging con número hasheado); P2 (capa LLM opcional de reformulación con guardas).

## Why

El productor de zona núcleo vive en WhatsApp: mandar un pin y elegir de un menú es más simple que abrir una web. El desafío pide explicar en lenguaje simple, y el canal tiene que ser confiable en una demo en vivo: si Twilio falla, un simulador web con el mismo motor conversacional garantiza que la demo funcione.

## What Changes

- Se agrega un motor conversacional determinista (máquina de estados): saludo, ubicación (pin de WhatsApp o texto lat,lon), rotación actual (menú numerado del catálogo), actor (menú), resultado resumido y opciones (ver detalle, cambiar actor, glosario, reiniciar).
- "Ver detalle" envía la tarjeta fija de 5 secciones de explanations (por qué se sugiere, evidencia, beneficios frente a la actual, faltantes, riesgos a revisar en el lote) cerrada con la leyenda "apoya, no reemplaza al agrónomo".
- Opción "ordenar la lista" (P1): primero las no riesgosas en agua o primero las de doble cultivo, usando el `display_order` de la api sin cambiar el ranking.
- Se agrega estado de sesión por número en memoria con TTL.
- Se agrega un adaptador de canal desacoplado: Twilio Sandbox detrás de una interfaz; el motor de rotaciones no conoce el canal.
- Se valida la firma de Twilio en POST /whatsapp/webhook.
- Se agrega el simulador web que usa POST /chat/simulate con el mismo motor conversacional.
- Se agrega una capa LLM opcional (apagada por defecto) que solo reformula texto, con guardas de números, cultivos y recomendaciones, y fallback a la plantilla.
- Secretos por `.env` y logging sin datos personales (número hasheado).

## Capabilities

### New Capabilities
- `whatsapp-channel`: flujo conversacional determinista, sesiones, adaptador Twilio, simulador, firma, capa LLM opcional con guardas y privacidad de logs.

### Modified Capabilities
- Ninguna.

## Impact

- `rastrojo.application.conversation` (motor conversacional puro) y `rastrojo.adapters.whatsapp` (Twilio, simulador, LLM opcional).
- Usa los casos de uso de evaluación de `api`/`application`, los textos WhatsApp y el glosario de `explanations`, y el catálogo de rotaciones y perfiles. El contrato HTTP común (errores, límites, rate limit) lo define `api`; `web-demo` hospeda la vista del simulador.
- Dependencias: SDK o validador de firma de Twilio; cliente HTTP del proveedor LLM solo si se habilita el flag.
- Visión futura: el mismo canal podría integrarse a PolPilot Agro; nada de su código ni endpoints se usa acá.

## Fuera de alcance

- Número de WhatsApp Business productivo y plantillas aprobadas por Meta (solo Sandbox).
- Audios, imágenes y lenguaje natural libre (solo texto de menú, coordenadas y pin).
- Persistencia de conversaciones e historial entre reinicios del servidor.
- Notificaciones salientes iniciadas por el sistema.
