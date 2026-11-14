# Spec Delta

## Purpose

Expone el motor, sus catálogos, el contexto NASA del lote, el glosario, los supuestos y los canales de chat por HTTP bajo `/api/v1`, con contratos validados, errores tipados y respuestas reproducibles.

## ADDED Requirements

### Requirement: Prefijo y contratos validados
Todos los endpoints MUST servirse bajo `/api/v1` y MUST validar request y response con modelos Pydantic estrictos (extra prohibido). Los endpoints son: POST /evaluate, GET /rotations/catalog, GET /actors/profiles, GET /plots/{plot_id}/context, GET /glossary, GET /assumptions, POST /whatsapp/webhook, POST /chat/simulate y GET /health.

#### Scenario: Campo extra en request
- **WHEN** se envía a POST /api/v1/evaluate un body válido con un campo adicional `foo`
- **THEN** la respuesta es 422 con `code` VALIDATION_ERROR y `details` que nombra el campo `foo`

#### Scenario: Ruta inexistente
- **WHEN** se pide GET /api/v1/unknown
- **THEN** la respuesta es 404 con `code` NOT_FOUND en el formato de error tipado

### Requirement: Formato de error tipado
Toda respuesta de error MUST ser JSON `{code, message, details}`, donde `code` pertenece a un catálogo cerrado, `message` es una frase en español rioplatense y `details` es un objeto o lista con información estructurada. Las respuestas de error MUST NOT incluir trazas de pila, rutas de archivos ni valores de configuración.

#### Scenario: Error interno sin traza
- **GIVEN** un fallo inesperado dentro del caso de uso
- **WHEN** se procesa el request
- **THEN** la respuesta es 500 con `code` INTERNAL_ERROR, sin traza de pila, y el log interno registra la traza con un id de request

### Requirement: Catálogo de códigos de error
El catálogo MUST incluir al menos, con su estado HTTP: VALIDATION_ERROR 422, MISSING_PARAMETER 422, UNKNOWN_ROTATION 422, UNKNOWN_ACTOR 422, OUT_OF_COVERAGE 422, PLOT_NOT_FOUND 404, NOT_FOUND 404, METHOD_NOT_ALLOWED 405, UNSUPPORTED_MEDIA_TYPE 415, PAYLOAD_TOO_LARGE 413, RATE_LIMITED 429, INVALID_SIGNATURE 403, DATA_UNAVAILABLE 503, CHANNEL_DISABLED 503, TIMEOUT 504, ENGINE_ERROR 500, INTERNAL_ERROR 500.

#### Scenario: Catálogo publicado
- **WHEN** se consulta el esquema OpenAPI
- **THEN** el componente del error declara `code` como enumeración con exactamente los códigos del catálogo

#### Scenario: Código fuera de catálogo
- **GIVEN** un handler que intenta responder con un código no catalogado
- **WHEN** corre el test de contrato de errores
- **THEN** el test falla

### Requirement: Evaluación con request completo
POST /evaluate MUST aceptar un request con `mode: "full"` que contiene un `EngineInput` ya resuelto, MUST correr el motor sin consultar caché y MUST responder con la salida del motor, la explicación en los formatos pedidos y el `input_hash`.

#### Scenario: EngineInput válido
- **GIVEN** el `EngineInput` de la fixture `demo-casilda`
- **WHEN** se envía a POST /api/v1/evaluate con `mode: "full"`
- **THEN** la respuesta es 200 con `engine_output`, `explanation` y `input_hash` igual al hash de esa entrada

### Requirement: Evaluación con request lite
POST /evaluate MUST aceptar `mode: "lite"` con lat, lon, rotación actual (id de catálogo o rotación definida válida), actor (OWNER, TENANT, COOP, BANK) y opcionalmente datos de suelo y superficie. La aplicación MUST resolverlo a un `EngineInput` usando solo caché, fixtures, parámetros con fuente y fecha y supuestos registrados.

#### Scenario: Lite en el lote de demo
- **GIVEN** DEMO_MODE=1 y coordenadas del lote `demo-casilda`
- **WHEN** se envía un request lite con rotación R_SOY_MONO y actor TENANT
- **THEN** la respuesta es 200 y `resolution` lista el origen de cada parte de la entrada (USER_INPUT, caché, fixture o ASSUMPTION con id)

#### Scenario: Actor desconocido
- **WHEN** se envía un request lite con actor `CONTRACTOR`
- **THEN** la respuesta es 422 con `code` UNKNOWN_ACTOR y `details` con los actores permitidos

#### Scenario: Rotación desconocida
- **WHEN** se envía un request lite con rotación actual `R_SUNFLOWER`
- **THEN** la respuesta es 422 con `code` UNKNOWN_ROTATION y `details` con los ids del catálogo

### Requirement: Reporte de resolución
La respuesta de una evaluación lite MUST incluir `resolution`: para cada parte de la entrada (lote, suelo, escenarios, parámetros económicos, perfil) su origen, el dataset o archivo usado y los faltantes que quedaron sin resolver. Los valores faltantes MUST NOT completarse con un default silencioso.

#### Scenario: Suelo no informado
- **GIVEN** un request lite sin datos de suelo y una caché sin suelo para esa celda
- **WHEN** se resuelve la entrada
- **THEN** `resolution` marca el suelo como faltante o como ASSUMPTION con id, y la explicación lo lista en faltantes

### Requirement: Cobertura geográfica
Una coordenada fuera del área soportada (bounding box de Argentina de `domain-models`, o fuera de las celdas habilitadas en DEMO_MODE) MUST responder OUT_OF_COVERAGE. Una coordenada dentro del área pero sin datos en caché MUST responder DATA_UNAVAILABLE con los datasets faltantes en `details`.

#### Scenario: Coordenada fuera de Argentina
- **WHEN** se envía un request lite con lat 40.7 y lon -74.0
- **THEN** la respuesta es 422 con `code` OUT_OF_COVERAGE

#### Scenario: Celda sin caché
- **GIVEN** una coordenada válida de Córdoba sin archivos en caché
- **WHEN** se envía un request lite
- **THEN** la respuesta es 503 con `code` DATA_UNAVAILABLE y `details.missing_datasets` lista por ejemplo NASA_POWER y SMAP_L4

### Requirement: Parámetro faltante
Si la entrada no puede resolverse porque falta un parámetro sin valor por defecto (por ejemplo un precio sin fuente), la respuesta MUST ser MISSING_PARAMETER con el nombre del parámetro y cómo proveerlo en `details`.

#### Scenario: Precio de maíz ausente
- **GIVEN** un archivo de parámetros económicos sin precio de maíz
- **WHEN** se evalúa un request lite que incluye R_MAIZE_SOY
- **THEN** la respuesta es 422 con `code` MISSING_PARAMETER y `details.parameter` nombra el precio de maíz

### Requirement: Idempotencia de evaluación
POST /evaluate MUST responder con el mismo body byte a byte ante el mismo request, serializado en JSON canónico, sin timestamps ni ids variables en el body. La respuesta MUST incluir los headers `X-Input-Hash` (hash del `EngineInput` resuelto) y `X-Engine-Version`.

#### Scenario: Dos requests iguales
- **WHEN** se envía dos veces el mismo request lite
- **THEN** ambos bodies son idénticos byte a byte y ambos `X-Input-Hash` coinciden con `input_hash` del body

#### Scenario: Orden de claves distinto
- **WHEN** se envían dos requests completos equivalentes con claves JSON en distinto orden
- **THEN** los bodies de respuesta son idénticos

### Requirement: Formatos de explicación pedidos
POST /evaluate MUST aceptar `explanation_formats` con valores en {structured, web, whatsapp} (por defecto structured y web) y MUST incluir solo los formatos pedidos. Pedir la comparación propietario vs arrendatario MUST hacer que la aplicación evalúe ambos perfiles.

#### Scenario: Solo WhatsApp
- **WHEN** se envía un request con `explanation_formats: ["whatsapp"]`
- **THEN** la explicación incluye solo la lista de mensajes WhatsApp

### Requirement: Catálogos de rotaciones y actores
GET /rotations/catalog MUST devolver las rotaciones del catálogo cerrado con id estable, nombre en español y campañas. GET /actors/profiles MUST devolver los perfiles OWNER, TENANT, COOP y BANK con H, α, λ, i y restricciones como valores con procedencia. Ambos MUST tener orden estable.

#### Scenario: Catálogo estable
- **WHEN** se pide GET /api/v1/rotations/catalog dos veces
- **THEN** ambas respuestas son idénticas y contienen R_SOY_MONO, R_MAIZE_SOY, R_WHEAT_SOY2_MAIZE, R_MAIZE_SOY_COVER y R_SOY_COVER

#### Scenario: Perfiles con supuestos
- **WHEN** se pide GET /api/v1/actors/profiles
- **THEN** cada parámetro de perfil tiene procedencia ASSUMPTION con id A-ACT-NN

### Requirement: Contexto NASA del lote
GET /plots/{plot_id}/context MUST devolver para un lote conocido sus series y resúmenes NASA en caché (lluvia, ET0, humedad SMAP, anomalía TWS GRACE-FO, NDVI) como valores con procedencia, resolución y limitación de cada dataset. Un id desconocido MUST responder PLOT_NOT_FOUND.

#### Scenario: Contexto del lote de demo
- **GIVEN** DEMO_MODE=1
- **WHEN** se pide GET /api/v1/plots/demo-casilda/context
- **THEN** la respuesta es 200 y cada dataset incluye `source` con período, resolución e `is_modeled`

#### Scenario: Lote inexistente
- **WHEN** se pide GET /api/v1/plots/no-existe/context
- **THEN** la respuesta es 404 con `code` PLOT_NOT_FOUND

### Requirement: Glosario y supuestos
GET /glossary MUST devolver el glosario de `explanations`. GET /assumptions MUST devolver el registro de supuestos con id, descripción, valor o rango, unidad, fuente y estado de validación, en orden por id.

#### Scenario: Supuestos pendientes visibles
- **WHEN** se pide GET /api/v1/assumptions
- **THEN** cada supuesto incluye `validation_status` y los PENDING_AFA se listan sin ocultarse

### Requirement: Health
GET /health MUST devolver estado del servicio, `engine_version`, versión de API, versión de plantillas, si DEMO_MODE está activo y estado de caché por dataset (OK, PARTIAL o EMPTY con cantidad de entradas). MUST responder sin correr el motor y sin acceso a red.

#### Scenario: Health con caché vacía
- **GIVEN** un directorio de caché vacío y DEMO_MODE=0
- **WHEN** se pide GET /api/v1/health
- **THEN** la respuesta es 200 con estado `degraded` y cada dataset con estado EMPTY

### Requirement: OpenAPI publicado
La API MUST publicar el esquema OpenAPI en `/api/v1/openapi.json` y documentación navegable en `/api/v1/docs`, con ejemplos de request lite y completo y todas las respuestas de error documentadas.

#### Scenario: Esquema exportable
- **WHEN** se pide GET /api/v1/openapi.json
- **THEN** la respuesta es un OpenAPI válido que incluye los nueve endpoints y el esquema de error

### Requirement: CORS para el front
La API MUST permitir CORS solo para los orígenes configurados por variable de entorno (front desplegado y desarrollo local), solo para GET, POST y OPTIONS, sin credenciales. Un origen no configurado MUST NOT recibir headers CORS de permiso.

#### Scenario: Origen permitido
- **GIVEN** el origen del front configurado
- **WHEN** el navegador hace un preflight OPTIONS a /api/v1/evaluate desde ese origen
- **THEN** la respuesta incluye `Access-Control-Allow-Origin` con ese origen

#### Scenario: Origen desconocido
- **WHEN** llega un preflight desde `https://otro.example`
- **THEN** la respuesta no incluye `Access-Control-Allow-Origin`

### Requirement: Sin secretos en respuestas
Las respuestas, incluidos health, errores y OpenAPI, MUST NOT contener valores de variables secretas (tokens de Twilio, claves de LLM, credenciales de Earthdata). La configuración secreta MUST leerse de `.env` y MUST existir `.env.example` sin valores.

#### Scenario: Escaneo de secretos
- **GIVEN** secretos de prueba cargados en el entorno
- **WHEN** un test recorre todos los endpoints con requests válidos e inválidos
- **THEN** ningún body ni header de respuesta contiene esos valores

### Requirement: Límite de tamaño
La API MUST rechazar bodies mayores al límite configurado por endpoint (por ejemplo 256 KB para /evaluate y 16 KB para /whatsapp/webhook y /chat/simulate) con PAYLOAD_TOO_LARGE, antes de parsear el JSON.

#### Scenario: Body excedido
- **WHEN** se envía a POST /api/v1/chat/simulate un body de 100 KB
- **THEN** la respuesta es 413 con `code` PAYLOAD_TOO_LARGE

### Requirement: Rate limit de endpoints públicos de chat
POST /whatsapp/webhook y POST /chat/simulate MUST aplicar un rate limit en memoria por cliente (IP, y número hasheado en el webhook) con límite configurable; al excederse MUST responder RATE_LIMITED con header `Retry-After`.

#### Scenario: Ráfaga de requests
- **GIVEN** un límite configurado de 30 requests por minuto
- **WHEN** un mismo cliente envía 31 requests a /chat/simulate en un minuto
- **THEN** el request 31 recibe 429 con `code` RATE_LIMITED y header `Retry-After`

### Requirement: Timeouts
POST /evaluate MUST cortar el procesamiento que exceda el timeout configurado y responder TIMEOUT. La API MUST NOT hacer requests de red salientes durante una evaluación.

#### Scenario: Evaluación lenta
- **GIVEN** un timeout configurado de 1 segundo y un motor de prueba que tarda 2 segundos
- **WHEN** se envía POST /api/v1/evaluate
- **THEN** la respuesta es 504 con `code` TIMEOUT

### Requirement: Content type
POST /evaluate y POST /chat/simulate MUST aceptar solo `application/json`; POST /whatsapp/webhook MUST aceptar solo `application/x-www-form-urlencoded`. Otro content type MUST responder UNSUPPORTED_MEDIA_TYPE.

#### Scenario: Evaluate con form
- **WHEN** se envía a POST /api/v1/evaluate un body form-urlencoded
- **THEN** la respuesta es 415 con `code` UNSUPPORTED_MEDIA_TYPE
