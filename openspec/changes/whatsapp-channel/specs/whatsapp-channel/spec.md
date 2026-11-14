# Spec Delta

## Purpose

Permite a un productor consultar por WhatsApp (o por un simulador web equivalente) la comparación de rotaciones de su lote mediante un flujo de menús determinista, con privacidad de datos y una capa opcional de reformulación que no puede alterar números ni recomendaciones.

## ADDED Requirements

### Requirement: Máquina de estados determinista
El flujo conversacional MUST ser una máquina de estados con estados GREETING, AWAIT_LOCATION, AWAIT_ROTATION, AWAIT_ACTOR, SHOW_RESULT, SHOW_DETAIL y SHOW_GLOSSARY. Dado el mismo estado de sesión, el mismo mensaje entrante y el mismo resultado de evaluación, MUST producir el mismo estado siguiente y los mismos mensajes salientes.

#### Scenario: Transición reproducible
- **GIVEN** una sesión en AWAIT_ACTOR con ubicación y rotación ya elegidas
- **WHEN** se procesa dos veces el mensaje "2" con el mismo resultado de evaluación
- **THEN** ambas veces el estado siguiente es SHOW_RESULT y los mensajes salientes son idénticos

### Requirement: Saludo e inicio
Un número sin sesión activa MUST recibir un saludo que explique en una frase qué hace la herramienta, las leyendas obligatorias de `explanations` y el pedido de ubicación, y la sesión MUST pasar a AWAIT_LOCATION.

#### Scenario: Primer mensaje
- **GIVEN** un número sin sesión
- **WHEN** envía "hola"
- **THEN** recibe el saludo con las leyendas y el pedido de ubicación, y la sesión queda en AWAIT_LOCATION

### Requirement: Ubicación por pin o texto
En AWAIT_LOCATION el sistema MUST aceptar un pin de ubicación de WhatsApp o texto con latitud y longitud en grados decimales (punto decimal separado por coma o espacio, o coma decimal separado por punto y coma). El texto "DEMO" MUST aceptarse siempre como el lote de demo. Una entrada inválida MUST repreguntar con un ejemplo; tras 3 intentos inválidos MUST ofrecer el lote de demo.

#### Scenario: Pin de WhatsApp
- **WHEN** en AWAIT_LOCATION llega un mensaje con Latitude -33.04 y Longitude -61.17
- **THEN** la ubicación se guarda y la sesión pasa a AWAIT_ROTATION con el menú de rotaciones

#### Scenario: Texto con coma decimal
- **WHEN** en AWAIT_LOCATION llega el texto "-33,04; -61,17"
- **THEN** se interpreta como lat -33.04 y lon -61.17

#### Scenario: Texto ambiguo
- **WHEN** en AWAIT_LOCATION llega el texto "-33,04,-61,17"
- **THEN** el sistema no adivina, repregunta y muestra los formatos aceptados

#### Scenario: Tres intentos inválidos
- **GIVEN** dos entradas de ubicación inválidas previas
- **WHEN** llega una tercera entrada inválida
- **THEN** el sistema ofrece responder "DEMO" para usar el lote de demostración

### Requirement: Cobertura de la ubicación
Si la ubicación está fuera de cobertura o sin datos en caché, el sistema MUST explicarlo en lenguaje simple con el motivo (OUT_OF_COVERAGE o DATA_UNAVAILABLE), MUST mantenerse en AWAIT_LOCATION y MUST ofrecer el lote de demo.

#### Scenario: Ubicación fuera de Argentina
- **WHEN** en AWAIT_LOCATION llega un pin con lat 40.7 y lon -74.0
- **THEN** el sistema responde que esa zona no está cubierta, ofrece "DEMO" y la sesión sigue en AWAIT_LOCATION

### Requirement: Menú de rotación actual
En AWAIT_ROTATION el sistema MUST mostrar un menú numerado con las rotaciones del catálogo en el orden de GET /rotations/catalog y MUST aceptar solo un número de opción válido; otra entrada MUST repetir el menú.

#### Scenario: Opción válida
- **GIVEN** el menú con R_SOY_MONO como opción 1
- **WHEN** el usuario responde "1"
- **THEN** la rotación actual queda R_SOY_MONO y la sesión pasa a AWAIT_ACTOR

#### Scenario: Opción fuera de rango
- **WHEN** en AWAIT_ROTATION el usuario responde "9" con un menú de 5 opciones
- **THEN** se repite el menú con la aclaración de responder con un número de la lista

### Requirement: Menú de actor
En AWAIT_ACTOR el sistema MUST mostrar un menú numerado con propietario, arrendatario, cooperativa y banco (OWNER, TENANT, COOP, BANK). Al elegir, MUST evaluar con la ubicación, la rotación y el actor elegidos y pasar a SHOW_RESULT.

#### Scenario: Elegir arrendatario
- **WHEN** en AWAIT_ACTOR el usuario responde "2"
- **THEN** se evalúa con actor TENANT y se envía el resultado resumido

### Requirement: Resultado resumido y opciones
En SHOW_RESULT el sistema MUST enviar el texto WhatsApp de `explanations` (particionado si excede el límite) seguido del menú: 1 ver detalle, 2 cambiar actor, 3 glosario, 4 reiniciar.

#### Scenario: Resultado con menú final
- **WHEN** termina una evaluación exitosa
- **THEN** el último mensaje enviado termina con el menú de 4 opciones y todos los mensajes respetan el límite de caracteres

### Requirement: Ver detalle
Desde SHOW_RESULT, la opción "ver detalle" MUST pedir el número de rotación del ranking y MUST enviar las cinco secciones de esa rotación en formato WhatsApp, volviendo luego al menú de resultado.

#### Scenario: Detalle de la primera rotación
- **GIVEN** una sesión en SHOW_DETAIL esperando rotación
- **WHEN** el usuario responde "1"
- **THEN** recibe por qué, evidencia, beneficios, faltantes y riesgos de la rotación en el puesto 1 y luego el menú de resultado

### Requirement: Cambiar actor
La opción "cambiar actor" MUST volver a AWAIT_ACTOR conservando ubicación y rotación actual, y al elegir otro actor MUST reevaluar y mostrar el nuevo resultado.

#### Scenario: De arrendatario a propietario
- **GIVEN** un resultado para TENANT
- **WHEN** el usuario elige "2" (cambiar actor) y luego "1" (propietario)
- **THEN** recibe el resultado para OWNER sin volver a pedir ubicación ni rotación

### Requirement: Glosario en el chat
La opción "glosario" MUST mostrar un menú numerado con los términos del glosario de `explanations` y, al elegir uno, MUST enviar su definición corta y volver al menú de glosario, con una opción para regresar al resultado.

#### Scenario: Definición de NDVI
- **GIVEN** la sesión en SHOW_GLOSSARY
- **WHEN** el usuario elige el número correspondiente a NDVI
- **THEN** recibe la definición corta de `ndvi` y el menú de glosario

### Requirement: Comandos globales
Los textos "reiniciar", "menu" y "ayuda" (sin distinguir mayúsculas ni tildes) MUST reconocerse en cualquier estado: reiniciar borra la sesión y saluda; menu repite el menú del estado actual; ayuda explica los comandos.

#### Scenario: Reiniciar a mitad del flujo
- **GIVEN** una sesión en AWAIT_ACTOR
- **WHEN** el usuario escribe "Reiniciar"
- **THEN** la sesión se borra y recibe el saludo inicial

### Requirement: Mensajes no soportados
Un mensaje con audio, imagen u otro adjunto distinto de ubicación MUST responderse con una frase fija que indique que solo se aceptan texto y ubicación, sin cambiar de estado.

#### Scenario: Audio recibido
- **WHEN** en AWAIT_ROTATION llega un mensaje de audio
- **THEN** se responde la frase fija y la sesión sigue en AWAIT_ROTATION

### Requirement: Sesión en memoria con TTL
El estado de sesión MUST guardarse en memoria por identificador de usuario del canal con un TTL configurable desde el último mensaje y un máximo de sesiones con desalojo de la menos reciente. Una sesión vencida MUST tratarse como nueva, avisando que se reinició.

#### Scenario: Sesión vencida
- **GIVEN** un TTL de 30 minutos y una sesión cuyo último mensaje fue hace 31 minutos
- **WHEN** el usuario envía "1"
- **THEN** recibe el aviso de sesión reiniciada y el saludo, y la sesión queda en AWAIT_LOCATION

### Requirement: Reintentos de Twilio sin efectos dobles
El adaptador MUST deduplicar mensajes entrantes por `MessageSid` durante el TTL de sesión: un reintento del mismo mensaje MUST NOT avanzar el estado otra vez.

#### Scenario: Webhook repetido
- **GIVEN** un mensaje "1" con MessageSid S ya procesado
- **WHEN** Twilio reenvía el mismo MessageSid S
- **THEN** el estado de sesión no cambia y no se reevalúa

### Requirement: Adaptador de canal desacoplado
El motor conversacional MUST depender solo de una interfaz de canal (mensaje entrante normalizado con id de usuario, texto, ubicación y tipo; lista de mensajes salientes). El motor de rotaciones y la generación de explicaciones MUST NOT conocer el canal.

#### Scenario: Mismo flujo en dos canales
- **GIVEN** la misma secuencia de mensajes normalizados
- **WHEN** se procesa por el adaptador Twilio y por el simulador
- **THEN** los textos salientes son idénticos y solo cambia el envoltorio (TwiML vs JSON)

### Requirement: Webhook de Twilio
POST /whatsapp/webhook MUST aceptar el formulario de Twilio, normalizarlo, procesarlo con el motor conversacional y responder TwiML con un elemento de mensaje por cada mensaje saliente. Ante un error interno MUST responder 200 con un mensaje fijo de disculpa y opción de reiniciar.

#### Scenario: Respuesta TwiML
- **WHEN** llega un webhook válido con el texto "hola"
- **THEN** la respuesta es 200, content type XML, con el saludo dentro de elementos de mensaje

#### Scenario: Error interno durante evaluación
- **GIVEN** un fallo inesperado del caso de uso de evaluación
- **WHEN** llega la elección de actor
- **THEN** la respuesta es 200 con el mensaje fijo de disculpa y la sesión no queda en un estado inválido

### Requirement: Validación de firma de Twilio
El webhook MUST validar el header `X-Twilio-Signature` con el auth token configurado y la URL pública configurada; una firma ausente o inválida MUST responder INVALID_SIGNATURE sin procesar el mensaje. Si el auth token no está configurado, el webhook MUST responder CHANNEL_DISABLED.

#### Scenario: Firma inválida
- **WHEN** llega un webhook con `X-Twilio-Signature` incorrecta
- **THEN** la respuesta es 403 con `code` INVALID_SIGNATURE y la sesión no se crea

#### Scenario: Canal sin configurar
- **GIVEN** que `TWILIO_AUTH_TOKEN` no está definido
- **WHEN** llega cualquier request al webhook
- **THEN** la respuesta es 503 con `code` CHANNEL_DISABLED

### Requirement: Simulador web
POST /chat/simulate MUST recibir `{session_id, text?, location?}` y responder `{messages, state, options}` usando el mismo motor conversacional que el webhook, con sesiones en un espacio de nombres separado del de WhatsApp. MUST funcionar con DEMO_MODE=1 y sin credenciales de Twilio.

#### Scenario: Flujo completo simulado
- **GIVEN** DEMO_MODE=1 sin variables de Twilio
- **WHEN** el simulador envía "hola", "DEMO", "1" y "2"
- **THEN** la última respuesta tiene `state` SHOW_RESULT y `messages` con el resumen y el menú final

#### Scenario: Sin texto ni ubicación
- **WHEN** se envía a /chat/simulate un body con solo `session_id`
- **THEN** la respuesta es 422 con `code` MISSING_PARAMETER

### Requirement: Capa LLM opcional apagada por defecto
La reformulación con LLM MUST estar desactivada salvo que `LLM_REPHRASE_ENABLED=true` y haya clave configurada. MUST aplicarse solo a textos de resultado y detalle, nunca a menús, leyendas ni marcas de supuestos, y MUST NOT ejecutarse dentro del motor de rotaciones.

#### Scenario: Flag apagado
- **GIVEN** la configuración por defecto
- **WHEN** se genera un resultado
- **THEN** no se hace ninguna llamada al proveedor LLM y el texto es el de la plantilla

### Requirement: Guarda de números en la reformulación
Con la capa LLM activa, el conjunto de números del texto reformulado (extraídos con el parser de formato argentino de `explanations`) MUST ser subconjunto del conjunto de números del texto de plantilla. Si no lo es, MUST usarse la plantilla.

#### Scenario: Número agregado
- **GIVEN** una plantilla con los números 1.235 y 3
- **WHEN** el LLM devuelve un texto que menciona 1.300
- **THEN** se descarta la reformulación y se envía la plantilla

#### Scenario: Número cambiado de formato
- **GIVEN** una plantilla con "1.235 USD/ha"
- **WHEN** el LLM devuelve "1235 USD/ha"
- **THEN** el parser lo normaliza al mismo valor y la guarda de números pasa

### Requirement: Guarda de cultivos y recomendaciones
Con la capa LLM activa, el texto reformulado MUST NOT mencionar cultivos o rotaciones ausentes en la plantilla (según el léxico del catálogo), MUST NOT contener expresiones prescriptivas de la lista de `explanations` y MUST conservar las leyendas y marcas de supuestos. Cualquier violación MUST producir fallback a la plantilla.

#### Scenario: Cultivo agregado
- **GIVEN** una plantilla que menciona solo soja y maíz
- **WHEN** el LLM devuelve un texto que menciona girasol
- **THEN** se envía la plantilla

#### Scenario: Recomendación agregada
- **WHEN** el LLM devuelve un texto con "te recomendamos sembrar maíz"
- **THEN** se envía la plantilla

### Requirement: Fallback ante falla o timeout del LLM
Ante error del proveedor, respuesta vacía, exceso del límite de caracteres o timeout configurado, el sistema MUST enviar el texto de plantilla sin demorar la respuesta más allá del timeout, y MUST registrar el motivo del fallback sin el contenido del texto.

#### Scenario: Timeout del proveedor
- **GIVEN** un timeout de 3 segundos y un proveedor que no responde
- **WHEN** se genera un resultado con la capa LLM activa
- **THEN** se envía la plantilla y el log registra `llm_fallback_reason=timeout`

### Requirement: Secretos por entorno
Las credenciales de Twilio, la clave del LLM y la sal de hash MUST leerse de variables de entorno (`.env` local) y MUST listarse sin valores en `.env.example`. Los secretos MUST NOT aparecer en logs, respuestas ni mensajes.

#### Scenario: Secreto en log
- **GIVEN** credenciales de prueba cargadas
- **WHEN** se ejecuta el flujo completo con logging en nivel DEBUG
- **THEN** ningún registro de log contiene esos valores

### Requirement: Logging sin datos personales
Los logs MUST identificar al usuario solo por un hash con sal del número de teléfono, MUST NOT registrar el número, el texto de los mensajes ni coordenadas exactas, y MUST registrar estado, transición, tipo de evento y resultado de cobertura.

#### Scenario: Número hasheado
- **WHEN** el número +5493410000000 completa el flujo
- **THEN** ningún log contiene "5493410000000" y todos los eventos de esa sesión comparten el mismo hash
