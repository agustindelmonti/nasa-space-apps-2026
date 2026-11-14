# Spec Delta

## Purpose

Garantizar que el lote de demo se pueda mostrar de punta a punta sin red ni credenciales, con datos NASA cacheados y trazables, salida del motor reproducible, verificación previa automatizada y un guion de presentación con plan B.

## ADDED Requirements

### Requirement: Lote de demo con ubicación supuesta
El sistema MUST definir un lote de demo con id `demo-casilda`, nombre, ubicación en el sur de Santa Fe y superficie, cuya ubicación y superficie MUST tener procedencia ASSUMPTION `A-DEMO-01` (placeholder a confirmar con el equipo) hasta que se reemplacen por un lote real confirmado.

#### Scenario: Lote demo marcado como supuesto
- **WHEN** se consulta `GET /api/v1/plots/demo-casilda/context`
- **THEN** la ubicación del lote se devuelve con procedencia ASSUMPTION y assumption_id `A-DEMO-01`

#### Scenario: Lote demo válido
- **WHEN** se valida el Lote `demo-casilda` contra los modelos de `domain-models`
- **THEN** la validación pasa y la ubicación está dentro del bounding box de Argentina

### Requirement: Fixtures NASA del lote demo
El repo MUST incluir en `data/fixtures/demo/` datos cacheados del lote demo para NASA POWER, SMAP L4, GPM IMERG, GRACE-FO y MODIS NDVI, en el formato validado de la caché de `nasa-ingestion`, cubriendo el período histórico que usa el motor.

#### Scenario: Fixtures completos
- **WHEN** se corre el test de completitud de fixtures
- **THEN** existe un archivo por dataset requerido y cada uno pasa la validación de esquema de la caché

#### Scenario: Período suficiente
- **WHEN** se arman los escenarios climáticos desde los fixtures
- **THEN** hay al menos un año en cada clase DRY, NORMAL y WET

### Requirement: Manifiesto de procedencia de fixtures
Los fixtures MUST tener un manifiesto versionado que registre por archivo: dataset, versión o colección, variable, período, resolución, fecha de descarga, URL o consulta de origen y checksum SHA-256. Un archivo sin entrada en el manifiesto o con checksum distinto MUST hacer fallar la verificación.

#### Scenario: Checksum alterado
- **GIVEN** un fixture modificado a mano sin actualizar el manifiesto
- **WHEN** se corre la verificación de fixtures
- **THEN** falla nombrando el archivo y ambos checksums

### Requirement: Parámetros económicos de ejemplo
El modo demo MUST proveer un archivo de parámetros económicos de ejemplo (precios, retenciones, costos, rindes por cultivo y clase de año) donde cada valor tenga procedencia ASSUMPTION con id del área DEMO (A-DEMO-02 a A-DEMO-06), fuente citada y fecha de referencia, y MUST rotularse como ejemplo, no recomendación.

#### Scenario: Parámetro sin fuente rechazado
- **GIVEN** un parámetro económico de ejemplo sin fuente o sin fecha
- **WHEN** se carga el archivo en modo demo
- **THEN** la carga falla indicando el parámetro

#### Scenario: Rótulo de ejemplo visible
- **WHEN** la API responde una evaluación en modo demo
- **THEN** los parámetros económicos aparecen con procedencia ASSUMPTION A-DEMO-NN y la respuesta indica que son valores de ejemplo

### Requirement: Flag DEMO_MODE sin red ni credenciales
Con `DEMO_MODE=1` la aplicación MUST arrancar sin credenciales de Earthdata, Twilio ni LLM y MUST resolver datos NASA, parámetros económicos y lote demo solo desde fixtures, sin abrir conexiones de red salientes.

#### Scenario: Arranque sin red
- **GIVEN** un entorno sin acceso a red y sin variables de credenciales
- **WHEN** se arranca la API con `DEMO_MODE=1` y se llama `POST /api/v1/evaluate` para `demo-casilda`
- **THEN** la respuesta es exitosa y un test que bloquea sockets salientes no registra intentos de conexión

#### Scenario: Health informa el modo
- **WHEN** se llama `GET /api/v1/health` con `DEMO_MODE=1`
- **THEN** la respuesta indica modo demo activo y versión de los fixtures

### Requirement: Lote fuera de la demo en modo demo
En modo demo, un pedido para un lote o coordenadas sin fixtures MUST responder un error tipado que indique que solo el lote demo está disponible offline, sin intentar descargar datos.

#### Scenario: Coordenadas sin fixtures
- **WHEN** con `DEMO_MODE=1` se pide una evaluación para lat -31.6, lon -60.7
- **THEN** la API responde un error tipado `{code, message, details}` con código de dato no disponible en modo demo

### Requirement: Regeneración de fixtures con diff
El repo MUST proveer un único comando que regenere los fixtures del lote demo desde las fuentes NASA (con credenciales del `.env`), actualice el manifiesto y reporte un diff por dataset (archivos cambiados, filas agregadas o quitadas, variación de estadísticos). Sin credenciales MUST fallar con mensaje claro sin tocar los fixtures.

#### Scenario: Sin credenciales
- **GIVEN** un entorno sin credenciales de Earthdata
- **WHEN** se corre el comando de regeneración
- **THEN** termina con error explicando la credencial faltante y los fixtures existentes quedan intactos

#### Scenario: Diff reportado
- **GIVEN** fuentes que devuelven un día más de datos que el fixture actual
- **WHEN** se corre la regeneración (con fuentes mockeadas en test)
- **THEN** el reporte lista el dataset cambiado y la cantidad de filas agregadas

### Requirement: Snapshot de la salida del motor para la demo
El repo MUST versionar la salida canónica del motor para `demo-casilda` con cada perfil OWNER, TENANT, COOP y BANK. Un test MUST comparar byte a byte la salida actual con el snapshot, incluidos `input_hash` y `engine_version`.

#### Scenario: Salida estable
- **WHEN** se corre el test de snapshot sin cambios en motor ni fixtures
- **THEN** las cuatro salidas coinciden byte a byte con el snapshot

#### Scenario: Cambio detectado
- **GIVEN** un cambio en un parámetro económico de ejemplo
- **WHEN** se corre el test de snapshot
- **THEN** el test falla mostrando el diff y exige actualizar el snapshot de forma explícita

#### Scenario: Rankings distintos por actor
- **WHEN** se comparan los snapshots de OWNER y TENANT
- **THEN** el test registra si el orden difiere; si no difiere, el checklist de pre-demo lo reporta como advertencia para revisar el guion

### Requirement: Imágenes estáticas de capas para el front
El modo demo MUST incluir imágenes estáticas de cada capa del mapa (NDVI, humedad SMAP L4, precipitación IMERG, base) recortadas al entorno del lote demo, con fecha, bounds y capa de origen en un JSON acompañante, generadas por el mismo comando de regeneración.

#### Scenario: Imagen con metadatos
- **WHEN** se corre la verificación de fixtures
- **THEN** cada imagen de capa tiene su JSON con capa GIBS, fecha y bounds, y los bounds contienen la ubicación del lote demo

### Requirement: Checklist de pre-demo automatizado
El repo MUST proveer un comando de pre-demo que verifique y reporte OK/FALLA por ítem: health de API (local y desplegada), modo demo, integridad de fixtures, snapshot, URL del front desplegado, respuesta de `/chat/simulate`, tile GIBS de muestra y existencia del video de respaldo. MUST terminar con código distinto de cero si falla un ítem crítico.

#### Scenario: API desplegada caída
- **GIVEN** la URL de la API desplegada sin responder
- **WHEN** se corre el comando de pre-demo
- **THEN** el reporte marca FALLA en ese ítem, sugiere el plan B local y el comando termina con código distinto de cero

#### Scenario: Todo en orden
- **GIVEN** API, front y fixtures sanos
- **WHEN** se corre el comando de pre-demo
- **THEN** todos los ítems salen OK y el comando termina con código cero en menos de 60 s

#### Scenario: Sin red en la sede
- **GIVEN** sin internet
- **WHEN** se corre el pre-demo en modo local
- **THEN** los ítems remotos se marcan como no disponibles y los locales (API en DEMO_MODE, fixtures, snapshot, video local) se verifican igual

### Requirement: Guion de demo de 4 minutos
El repo MUST incluir un guion en `docs/demo/` con bloques y tiempos que sumen como máximo 4 minutos, en este orden: problema; lote en mapa con capas NASA; agua invisible (GRACE-FO, SMAP, IMERG); ranking propietario vs arrendatario; evidencia y faltantes; WhatsApp; cierre honesto y visión PolPilot Agro. Cada bloque MUST indicar qué se muestra, qué se dice y quién lo dice.

#### Scenario: Tiempos cerrados
- **WHEN** se suman los tiempos de los bloques del guion
- **THEN** el total es menor o igual a 4:00 y los 7 bloques están en el orden indicado

#### Scenario: Cierre honesto
- **WHEN** se lee el bloque de cierre
- **THEN** menciona "apoya, no reemplaza al agrónomo", "escenarios históricos, no predicción", los supuestos pendientes de AFA, el uso de IA y PolPilot solo como visión

### Requirement: Plan B de la demo
El guion MUST incluir un plan B con disparadores y acciones: si falla la red o el deploy, correr API en DEMO_MODE y front en local; si falla también el equipo local, reproducir el video grabado de la demo. El video de respaldo MUST estar disponible offline en la máquina de presentación.

#### Scenario: Deploy caído durante el pitch
- **GIVEN** la URL pública del front no carga
- **WHEN** el presentador sigue el plan B
- **THEN** el guion indica el comando exacto para levantar API y front locales en DEMO_MODE y el tiempo máximo para decidir pasar al video

### Requirement: Material para el video de YouTube
El repo MUST incluir en `docs/demo/` un guion del video de YouTube (duración objetivo según bases del desafío), lista de tomas basada en el flujo de la demo, textos en pantalla con las leyendas de comunicación honesta, créditos de datos NASA y librerías, y declaración de uso de IA.

#### Scenario: Créditos completos
- **WHEN** se revisa el material del video
- **THEN** lista cada dataset NASA usado con su nombre oficial y declara el uso de IA (Claude Code)
