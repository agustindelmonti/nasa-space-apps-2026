# Spec Delta

## Purpose

Presentar en una web responsive el análisis de rotaciones de un lote: mapa con capas NASA, ranking por actor con desglose, evidencia con procedencia, glosario y simulador de chat, sin calcular nada del motor en el navegador.

## ADDED Requirements

### Requirement: El front solo presenta
La web MUST obtener todo puntaje, rango, desglose, factibilidad, ΔSuelo, riesgo, evidencia y texto explicativo desde la API `/api/v1`. La web MUST NOT calcular, reordenar por su cuenta ni redondear de forma distinta a la API ningún resultado del motor; solo formatea unidades para mostrar.

#### Scenario: Ranking tal como llega de la API
- **GIVEN** una respuesta mockeada de `POST /api/v1/evaluate` con rangos 1, 2, 3 asignados a R_MAIZE_SOY, R_SOY_MONO, R_WHEAT_SOY2_MAIZE
- **WHEN** la tabla se renderiza (test Playwright con la API interceptada)
- **THEN** las filas aparecen exactamente en ese orden con los puntajes recibidos, sin recalcular

#### Scenario: Sin lógica de motor en el bundle
- **WHEN** se inspecciona el código fuente de `web/src`
- **THEN** no existe ninguna implementación de la función objetivo, del descuento ni del cálculo de riesgo (verificado por revisión y por un test que falla si aparece un módulo `score`/`npv` en el front)

### Requirement: Mapa del lote con capas NASA GIBS
La web MUST mostrar un mapa centrado en el lote (marcador o polígono) con al menos tres capas NASA superponibles servidas por GIBS WMTS: NDVI MODIS (compuesto 8 o 16 días), humedad de suelo SMAP L4 y precipitación GPM IMERG, más una capa base. El usuario MUST poder activar y desactivar cada capa y ajustar su opacidad.

#### Scenario: Capas disponibles
- **GIVEN** el lote `demo-casilda` cargado
- **WHEN** el usuario abre el selector de capas
- **THEN** ve las capas NDVI MODIS, Humedad de suelo SMAP L4 y Precipitación IMERG, cada una con un control de visibilidad

#### Scenario: Pedido de tiles a GIBS
- **WHEN** el usuario activa la capa NDVI con fecha 2024-01-15
- **THEN** el navegador pide tiles a `gibs.earthdata.nasa.gov/wmts/epsg3857/best/` con el identificador de capa configurado y el parámetro de tiempo correspondiente (verificable interceptando requests en Playwright)

### Requirement: Fecha seleccionable por capa
La web MUST permitir elegir la fecha de las capas GIBS con un selector de fecha acotado al período disponible de cada capa. La fecha MUST ajustarse a la granularidad del producto (por ejemplo, el inicio del compuesto de 8 o 16 días) y la fecha efectivamente pedida MUST mostrarse en la leyenda.

#### Scenario: Fecha fuera de rango
- **WHEN** el usuario elige una fecha anterior al inicio de la serie de SMAP L4
- **THEN** la web no pide tiles para esa fecha y muestra un aviso con el rango disponible

#### Scenario: Ajuste a compuesto
- **GIVEN** la capa NDVI de compuesto multi-día activa
- **WHEN** el usuario elige un día que no es inicio de compuesto
- **THEN** la leyenda muestra la fecha del compuesto efectivamente pedido

### Requirement: Leyenda, resolución y limitación de cada capa
Cada capa activa MUST mostrar leyenda de colores con unidad, dataset de origen, resolución espacial y temporal, y una limitación en lenguaje simple (por ejemplo, SMAP L4 es modelado a ~9 km y no ve el lote individual). Los textos MUST venir de configuración versionada o de `GET /plots/{id}/context`, no del código de componentes.

#### Scenario: Limitación visible
- **WHEN** el usuario activa la capa de humedad SMAP L4
- **THEN** la leyenda muestra unidad, resolución aproximada (~9 km, ejemplo de texto de configuración) y una frase de limitación

### Requirement: Fallback de capas sin GIBS
Si los tiles de GIBS fallan (error de red o timeout configurable), la web MUST mostrar para el lote demo una imagen estática cacheada de cada capa (de `demo-mode`) con un indicador visible "imagen cacheada" y la fecha de la imagen. Para lotes sin imagen cacheada MUST mostrar un aviso claro.

#### Scenario: GIBS caído en la demo
- **GIVEN** las requests a `gibs.earthdata.nasa.gov` bloqueadas en Playwright
- **WHEN** se carga el lote `demo-casilda` con la capa NDVI activa
- **THEN** se ve la imagen estática del lote con el rótulo "imagen cacheada" y su fecha, y la página no muestra errores no manejados

### Requirement: Tabla comparativa de rotaciones
La web MUST mostrar una tabla con al menos 3 rotaciones evaluadas, incluida la actual, con rango, nombre, puntaje total en USD/ha y su desglose (VAN, α·ΔSuelo, λ·Riesgo, términos de prioridad), diferencia contra la actual (`score_delta_vs_current`), factibilidad hídrica, ΔSuelo y Riesgo. La rotación con `is_current` MUST quedar destacada con rótulo textual "actual", no solo por color.

#### Scenario: Rotación actual destacada
- **GIVEN** una evaluación donde R_SOY_MONO tiene `is_current=true`
- **WHEN** se renderiza la tabla
- **THEN** su fila muestra el rótulo "actual" y un estilo diferenciado

#### Scenario: Menos de 3 resultados
- **WHEN** la API devuelve menos de 3 rotaciones
- **THEN** la web muestra un aviso de evaluación incompleta en lugar de una tabla parcial sin explicación

### Requirement: Factibilidad hídrica con texto
La factibilidad MUST mostrarse con ícono, color y texto (Factible, Riesgosa, No factible) y su porqué tal como lo envía la API. Una rotación NOT_FEASIBLE MUST seguir visible en la tabla con su motivo.

#### Scenario: Rotación no factible
- **WHEN** la API marca R_WHEAT_SOY2_MAIZE como NOT_FEASIBLE con un motivo
- **THEN** la fila muestra "No factible" y el motivo es accesible desde la fila

### Requirement: Selector de actor
La web MUST ofrecer un selector con los perfiles OWNER (Propietario), TENANT (Arrendatario), COOP (Cooperativa) y BANK (Banco) obtenidos de `GET /actors/profiles`. Al cambiar de actor MUST pedir una nueva evaluación a la API y cargar los valores H, α, λ del perfil en los sliders.

#### Scenario: Propietario vs arrendatario
- **GIVEN** la evaluación con actor OWNER mostrada
- **WHEN** el usuario elige TENANT
- **THEN** la web llama `POST /api/v1/evaluate` con el actor TENANT, actualiza la tabla con la respuesta y los sliders muestran los valores del perfil TENANT

### Requirement: Sliders H, α y λ recalculados por la API
La web MUST ofrecer sliders para H (años), α y λ dentro de los rangos que informa la API. Cada cambio MUST enviarse a `POST /evaluate` con debounce y la web MUST mostrar estado de carga; ante respuestas fuera de orden MUST mostrar solo la del último pedido.

#### Scenario: Cambio de λ
- **WHEN** el usuario mueve λ y suelta el slider
- **THEN** se envía un único pedido a `/evaluate` con el nuevo λ y la tabla se actualiza con la respuesta

#### Scenario: Respuestas fuera de orden
- **GIVEN** dos pedidos sucesivos donde el primero responde después del segundo (latencia simulada en Playwright)
- **WHEN** llegan ambas respuestas
- **THEN** la tabla refleja la respuesta del segundo pedido

### Requirement: Indicador de cambio de ranking
Tras cada nueva evaluación la web MUST indicar, por rotación, el cambio de posición respecto de la evaluación anterior (por ejemplo, flecha y "+1", "-2", "=") y MUST animar el reordenamiento salvo que el usuario prefiera movimiento reducido.

#### Scenario: Subida de posición
- **GIVEN** R_MAIZE_SOY en rango 2 con actor TENANT
- **WHEN** se cambia a OWNER y la API la devuelve en rango 1
- **THEN** su fila muestra un indicador de subida "+1"

#### Scenario: Movimiento reducido
- **GIVEN** el navegador con `prefers-reduced-motion: reduce`
- **WHEN** cambia el ranking
- **THEN** la tabla se reordena sin animación y el indicador textual sigue visible

### Requirement: Badge de procedencia por número
Cada número del análisis mostrado (puntaje, términos, ΔSuelo, riesgo, datos NASA, parámetros) MUST llevar un badge con su procedencia OBSERVED, DERIVED, ASSUMPTION o USER_INPUT, distinguible por texto o ícono además de color.

#### Scenario: Supuesto marcado
- **GIVEN** un precio de ejemplo con procedencia ASSUMPTION `A-DEMO-02`
- **WHEN** se muestra en el panel
- **THEN** el valor lleva el badge ASSUMPTION

### Requirement: Tooltip de procedencia
Al pasar el mouse, enfocar con teclado o tocar un badge, la web MUST mostrar: para OBSERVED/DERIVED, dataset, variable, período y resolución (y para DERIVED, insumos y método); para ASSUMPTION, assumption_id, descripción, fuente y estado de validación (desde `GET /assumptions`); para USER_INPUT, que lo cargó el usuario.

#### Scenario: Tooltip de dato SMAP
- **WHEN** el usuario enfoca con teclado el badge de la humedad inicial
- **THEN** el tooltip muestra dataset SMAP_L4, variable, período y resolución

#### Scenario: Tooltip de supuesto
- **WHEN** el usuario toca el badge de un valor ASSUMPTION en celular
- **THEN** se muestra el assumption_id, su fuente o "pendiente AFA" y su estado de validación

### Requirement: Panel de evidencia, faltantes y riesgos
Al seleccionar una rotación la web MUST mostrar su evidencia (dataset, variable, período, valor e interpretación), beneficios, faltantes de información (qué falta, por qué importa, cómo conseguirlo) y riesgos con severidad, tal como los envía la API.

#### Scenario: Faltantes visibles
- **GIVEN** una evaluación donde falta la profundidad de napa
- **WHEN** el usuario abre el panel de la rotación con cultivo de servicio
- **THEN** ve el faltante "profundidad de napa" con por qué importa y cómo conseguirlo

### Requirement: Glosario en lenguaje simple
La web MUST ofrecer un glosario obtenido de `GET /glossary` que incluya al menos evapotranspiración, anomalía de humedad, NDVI, helada, estrés térmico, balance hídrico, GRACE-FO y la diferencia entre dato satelital y medición de campo. Los términos del glosario que aparezcan en la UI MUST enlazar a su definición.

#### Scenario: Término enlazado
- **WHEN** el usuario activa el término "NDVI" en la leyenda del mapa
- **THEN** se abre la definición del glosario de NDVI

### Requirement: Simulador de chat WhatsApp
La web MUST incluir un simulador de chat con apariencia de mensajería que envía cada mensaje a `POST /api/v1/chat/simulate` y muestra la respuesta textual tal cual. MUST permitir enviar una ubicación de ejemplo (lote demo) y la rotación actual, y MUST rotularse como simulación.

#### Scenario: Conversación de demo
- **WHEN** el usuario envía "hola" y luego la ubicación del lote demo
- **THEN** se muestran las respuestas de `/chat/simulate` en orden, con el rótulo "Simulación del canal WhatsApp"

#### Scenario: Error del simulador
- **WHEN** `/chat/simulate` responde un error tipado `{code, message}`
- **THEN** el chat muestra un mensaje de error comprensible y permite reintentar

### Requirement: Leyendas de comunicación honesta
La web MUST mostrar en todo momento, visibles sin scroll en escritorio y en el pie en celular, las leyendas "Apoya, no reemplaza al agrónomo" y "Escenarios históricos, no predicción".

#### Scenario: Leyendas siempre presentes
- **WHEN** se carga cualquier vista en viewport 1920x1080 y en 390x844
- **THEN** ambas leyendas están en el DOM y visibles (assert de Playwright)

### Requirement: Diseño responsive para proyector y celular
La web MUST ser usable en viewport de proyector (1920x1080 y 1280x720) con mapa y tabla visibles a la vez, y en celular (390x844) con secciones apiladas, sin scroll horizontal de página.

#### Scenario: Celular sin scroll horizontal
- **WHEN** se carga la web en 390x844
- **THEN** el ancho del documento no supera el viewport y la tabla se presenta como tarjetas o con scroll interno propio

#### Scenario: Proyector
- **WHEN** se carga la web en 1280x720
- **THEN** el mapa y la tabla de rotaciones son visibles sin scroll

### Requirement: Accesibilidad básica
La web MUST ser operable con teclado (selector de actor, sliders, capas, tabla, badges, chat), MUST tener etiquetas accesibles en controles, contraste mínimo WCAG AA en texto y MUST no transmitir información solo por color. MUST pasar un chequeo automático axe sin violaciones críticas.

#### Scenario: Chequeo axe
- **WHEN** se corre axe sobre la vista principal con Playwright
- **THEN** no hay violaciones de impacto "critical" ni "serious"

#### Scenario: Sliders con teclado
- **WHEN** el usuario enfoca el slider λ y presiona flecha derecha
- **THEN** el valor cambia y su valor actual se anuncia mediante atributos ARIA

### Requirement: Estados de API y modo demo
La web MUST leer la URL de la API de configuración de build, MUST consultar `GET /health` al iniciar y MUST mostrar un indicador si la API está en modo demo o caída. En modo demo MUST funcionar sin red externa salvo tiles GIBS.

#### Scenario: API en modo demo
- **GIVEN** `GET /health` responde con modo demo activo
- **WHEN** se carga la web
- **THEN** se ve un indicador "Modo demo (datos cacheados)"

#### Scenario: API caída
- **WHEN** `GET /health` falla
- **THEN** la web muestra un estado de error con instrucción de reintento y no queda en blanco

#### Scenario: Sin otras salidas de red
- **GIVEN** Playwright bloqueando todo host salvo la API y `gibs.earthdata.nasa.gov`
- **WHEN** se recorre el flujo completo de demo
- **THEN** no hay requests bloqueadas ni errores en consola

### Requirement: Calendario de suelo desnudo
Al seleccionar una rotación la web MUST mostrar su calendario de 12 meses de días sin cultivo vivo y sin cobertura tal como lo envía la API y, para la rotación actual, la fracción observada de NDVI bajo umbral del lote como fila de evidencia con badge OBSERVED. La web MUST NOT calcular días ni fracciones.

#### Scenario: Calendario de la actual con NDVI
- **GIVEN** una respuesta mockeada con calendario de suelo desnudo y evidencia NDVI para la actual
- **WHEN** se selecciona la rotación actual
- **THEN** se ven 12 celdas con los días de la API y la fila de NDVI observado con su badge y tooltip de dataset y período

#### Scenario: Comparar con una alternativa
- **WHEN** se selecciona una rotación con cultivo de servicio
- **THEN** su calendario muestra los valores de la API y no tiene fila de NDVI observado

### Requirement: Timeline de vulnerabilidad
La web MUST mostrar, por cultivo de la rotación seleccionada, un timeline mensual con los eventos que envía la API (helada y déficit hídrico en P0; estrés térmico y lluvia extrema en P1) y su nivel por texto o ícono además de color, con los meses fuera del ciclo marcados y el umbral como tooltip de supuesto.

#### Scenario: Déficit en enero
- **GIVEN** una respuesta con déficit HIGH en enero para la soja de segunda
- **WHEN** se abre el timeline de esa rotación
- **THEN** la celda de enero de la soja de segunda muestra "alto" con su frecuencia y el tooltip cita el supuesto del umbral

#### Scenario: Evento ausente
- **WHEN** la respuesta no trae lluvia extrema porque falta IMERG
- **THEN** el timeline no muestra esa fila y el panel de faltantes muestra el Faltante enviado por la API

### Requirement: Rango entre años secos y húmedos
Para cada rotación la web MUST mostrar el rango de margen por clase de año (mínimo, esperado, máximo de DRY, NORMAL y WET) y el rango hídrico por clase que envía la API, con una leyenda que diga que así se expresa la incertidumbre.

#### Scenario: Barras de rango
- **GIVEN** una respuesta con rangos de margen por clase
- **WHEN** se abre el panel de la rotación
- **THEN** se ven tres barras rotuladas Seco, Normal y Húmedo con mínimo, esperado y máximo tal como los envía la API

### Requirement: Filtro por clase de año y prioridades
La web MUST ofrecer un filtro de clase de año (Todos, Solo secos, Solo húmedos) y controles de prioridades del productor que se envían a `POST /evaluate`, y MUST mostrar el filtro efectivo y los años usados que declara la respuesta.

#### Scenario: Solo años secos
- **WHEN** el usuario elige "Solo secos"
- **THEN** se envía `year_class_filter: "DRY"` a `/evaluate` y la tabla muestra el rótulo del filtro y la cantidad de años usados según la respuesta

#### Scenario: Prioridad de agua
- **WHEN** el usuario sube la prioridad de agua
- **THEN** se envía un único pedido con la prioridad y la tabla muestra el término de prioridad que devuelve la API
