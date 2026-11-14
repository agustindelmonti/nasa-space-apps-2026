# Spec Delta

## Purpose

Convierte la salida determinista del motor en explicaciones en lenguaje simple (por qué, evidencia, beneficios, faltantes y riesgos de cada rotación), con cada número trazable a su procedencia, en formatos para API, web y WhatsApp.

## ADDED Requirements

### Requirement: Generación determinista por plantillas
Las explicaciones MUST generarse con plantillas deterministas a partir de la salida del motor y su entrada resuelta, sin LLM, red, reloj ni aleatoriedad. Misma salida del motor y mismas opciones de formato MUST producir el mismo texto byte a byte.

#### Scenario: Mismo resultado, mismo texto
- **GIVEN** una salida del motor con un `input_hash` dado
- **WHEN** se generan las explicaciones dos veces, en procesos distintos
- **THEN** los tres formatos de salida son idénticos byte a byte

#### Scenario: Sin acceso a red
- **GIVEN** un entorno de test sin red
- **WHEN** se generan las explicaciones de una salida del motor de fixture
- **THEN** la generación termina sin intentar ninguna conexión

### Requirement: Explicación por rotación
Para cada rotación, la explicación MUST ser una tarjeta fija con cinco secciones en este orden: por qué se sugiere, evidencia, beneficios frente a la actual, faltantes de información y riesgos a revisar en el lote. Una sección vacía MUST mostrarse con una frase fija, nunca omitirse. Cada tarjeta MUST cerrar con la leyenda "Esta herramienta apoya, no reemplaza, al agrónomo." en todos los formatos.

#### Scenario: Cinco secciones presentes
- **GIVEN** una salida del motor con 4 rotaciones evaluadas
- **WHEN** se genera la explicación estructurada
- **THEN** cada rotación tiene las secciones `why`, `evidence`, `benefits`, `missing_info` y `risks` en ese orden

#### Scenario: Tarjeta cierra con la leyenda
- **WHEN** se genera la tarjeta de cualquier rotación en formato estructurado, web o WhatsApp
- **THEN** las cinco secciones aparecen en orden y la última línea de la tarjeta es la leyenda "Esta herramienta apoya, no reemplaza, al agrónomo."

#### Scenario: Faltantes vacíos
- **GIVEN** una rotación cuya lista de faltantes está vacía en la salida del motor
- **WHEN** se genera el texto web
- **THEN** la sección de faltantes muestra la frase fija de "sin faltantes registrados" y no inventa ninguno

### Requirement: Sección por qué
La sección "por qué" MUST indicar la posición de la rotación en el ranking, si es la rotación actual, su estado de factibilidad hídrica y el término dominante del puntaje (el de mayor valor absoluto entre VAN del margen, término de suelo y término de riesgo), nombrándolo en lenguaje simple. Las comparaciones sin número en la salida del motor MUST ser cualitativas.

#### Scenario: Término dominante de suelo
- **GIVEN** una rotación con desglose donde el término de suelo tiene el mayor valor absoluto
- **WHEN** se genera la sección por qué
- **THEN** el texto atribuye la posición principalmente al efecto sobre el suelo y cita el valor de ese término tal como figura en la salida

#### Scenario: Rotación no factible
- **GIVEN** una rotación con factibilidad NOT_FEASIBLE
- **WHEN** se genera la sección por qué
- **THEN** el texto dice explícitamente que en los escenarios históricos evaluados no hay agua suficiente para esa rotación, independientemente de su puntaje

#### Scenario: Factibilidad desconocida
- **GIVEN** una rotación con factibilidad UNKNOWN y un Faltante de años con clima completo
- **WHEN** se genera la sección por qué
- **THEN** el texto dice que la factibilidad hídrica es "desconocida" por falta de datos, nombra el faltante y no usa "no apta", "no factible" ni un porcentaje

#### Scenario: Diferencia contra la actual citada
- **GIVEN** una rotación con `score_delta_vs_current` = 65 USD/ha en la salida del motor
- **WHEN** se compara con la actual
- **THEN** el texto cita "65 USD/ha más que la actual" con la ruta a `score_delta_vs_current` y no calcula la diferencia

#### Scenario: Comparación sin número disponible
- **GIVEN** que la salida no trae `score_delta_vs_current` (la actual no tiene puntaje)
- **WHEN** se compara una rotación con la actual
- **THEN** el texto usa una comparación cualitativa ("más alto", "más bajo") y no calcula la diferencia

### Requirement: Sección de evidencia
Cada evidencia MUST mostrar dataset, variable, período, valor con unidad, interpretación y la limitación del dato (resolución espacial y si es modelado), tomadas de la salida del motor y del catálogo de datasets de `nasa-ingestion`, nunca escritas a mano en la plantilla.

#### Scenario: Evidencia de humedad SMAP
- **GIVEN** una evidencia de humedad de zona de raíces de SMAP L4 en la salida del motor
- **WHEN** se genera el texto web
- **THEN** el texto nombra SMAP L4, la variable, el período, el valor con unidad, la interpretación y que es un dato modelado de píxel de varios kilómetros, no una medición del lote

### Requirement: Beneficios, faltantes y riesgos
Los beneficios MUST provenir de la salida del motor. Cada faltante MUST decir qué dato falta, por qué importa y cómo conseguirlo. Cada riesgo MUST decir tipo, severidad en palabras (bajo, medio, alto) y su base (evidencia o supuesto con su id).

#### Scenario: Riesgo basado en supuesto
- **GIVEN** un riesgo de helada con severidad MEDIUM cuya base es el umbral de helada A-CLI-05
- **WHEN** se genera el texto web
- **THEN** el riesgo se muestra como "riesgo de helada: medio" seguido de la marca de supuesto A-CLI-05

### Requirement: Trazabilidad de números citados
Todo número que aparezca en un texto generado MUST existir en la salida del motor o en su entrada resuelta con el mismo `input_hash`, y MUST registrarse como cita con la ruta al campo de origen y su procedencia. El generador MUST NOT hacer cálculos que produzcan números nuevos para el texto.

#### Scenario: Test de extracción de números
- **GIVEN** las explicaciones generadas para una salida del motor de fixture
- **WHEN** un test extrae todos los números del texto web y del texto WhatsApp con el parser de formato argentino
- **THEN** cada número extraído coincide con el valor formateado de alguna cita, y la ruta de esa cita resuelve a un campo con procedencia en la salida o entrada del motor

#### Scenario: Número inventado detectado
- **GIVEN** una plantilla modificada que escribe un número fijo que no está en la salida del motor
- **WHEN** corre el test de trazabilidad
- **THEN** el test falla nombrando el número y la plantilla

### Requirement: Tokens con dígitos permitidos
Los tokens con dígitos exentos de cita MUST pertenecer a una lista cerrada y versionada: ids de supuestos (`A-<AREA>-<NN>`), marcadores de partición de mensajes (`n/m`), números de opción de menú y nombres propios fijos (por ejemplo "soja de 2da", "GRACE-FO"). El test de trazabilidad MUST excluir solo esos tokens.

#### Scenario: Id de supuesto no cuenta como número
- **GIVEN** un texto que contiene la marca de supuesto A-ECO-03
- **WHEN** corre el test de trazabilidad
- **THEN** el token A-ECO-03 se excluye y no exige cita

### Requirement: Marcado visible de supuestos
Todo número cuya procedencia sea ASSUMPTION MUST mostrarse con una marca visible que incluya su `assumption_id` en el texto web y una marca abreviada con nota al pie que liste los ids en el texto WhatsApp. La explicación estructurada MUST listar todos los supuestos usados con su estado de validación.

#### Scenario: Precio supuesto en texto web
- **GIVEN** un margen que depende de un rinde de ejemplo con procedencia ASSUMPTION A-DEMO-06
- **WHEN** se genera el texto web
- **THEN** el número aparece seguido de "(supuesto A-DEMO-06)"

#### Scenario: Supuestos en WhatsApp
- **GIVEN** un resumen WhatsApp que cita dos números supuestos
- **WHEN** se genera el texto corto
- **THEN** cada número lleva un asterisco y el último mensaje incluye la línea "* Supuestos a validar con AFA:" con los ids

### Requirement: Resumen comparativo
La explicación MUST incluir un resumen comparativo que liste las rotaciones en orden de ranking con posición, nombre, puntaje, factibilidad y marca de rotación actual, y que indique en qué posición quedó la rotación actual.

#### Scenario: Rotación actual en tercer lugar
- **GIVEN** una salida donde la rotación actual R_SOY_MONO quedó tercera
- **WHEN** se genera el resumen comparativo
- **THEN** el resumen dice que la rotación actual quedó en el puesto 3 y lista primero las dos que quedaron arriba

### Requirement: Propietario vs arrendatario
Cuando la aplicación provee dos salidas del motor para el mismo lote con perfiles OWNER y TENANT, la explicación MUST incluir la sección "qué cambia si sos propietario vs arrendatario", con la posición de cada rotación en ambos rankings y el término del puntaje que explica cada cambio de posición. Si falta una de las dos salidas, la sección MUST omitirse con una nota fija.

#### Scenario: Ranking que cambia por horizonte
- **GIVEN** dos salidas del mismo lote donde R_MAIZE_SOY_COVER es primera para OWNER y cuarta para TENANT
- **WHEN** se genera la sección propietario vs arrendatario
- **THEN** el texto dice ambas posiciones y atribuye la diferencia al término de suelo o al horizonte, según el desglose de cada salida

#### Scenario: Salidas de lotes distintos
- **GIVEN** dos salidas cuyos lotes no coinciden
- **WHEN** se pide la sección comparativa
- **THEN** la generación falla con un error tipado en lugar de comparar

### Requirement: Leyendas obligatorias
Todo texto web y todo resultado WhatsApp MUST incluir, sin modificaciones, las leyendas "Esta herramienta apoya, no reemplaza, al agrónomo." y "Son escenarios con años históricos, no una predicción.". La explicación estructurada MUST incluirlas en un campo `disclaimers`.

#### Scenario: Leyendas en WhatsApp particionado
- **GIVEN** un resumen WhatsApp que se divide en 3 mensajes
- **WHEN** se generan los mensajes
- **THEN** ambas leyendas aparecen completas en el último mensaje

### Requirement: Lenguaje no prescriptivo
Los textos MUST describir resultados de escenarios y MUST NOT ordenar, garantizar, predecir ni expresar confianza en porcentaje. Un test MUST rechazar una lista cerrada y versionada de expresiones prohibidas que incluye al menos "te recomendamos", "tenés que", "garantiza", "predice", "va a llover", "% de confianza" y "confianza del".

#### Scenario: Expresión prohibida en plantilla
- **GIVEN** una plantilla que contiene "tenés que sembrar"
- **WHEN** corre el test de lenguaje
- **THEN** el test falla nombrando la plantilla y la expresión

#### Scenario: Porcentaje de confianza prohibido
- **GIVEN** una plantilla que escribe "85 % de confianza" o "el modelo predice"
- **WHEN** corre el test de lenguaje
- **THEN** el test falla nombrando la expresión

### Requirement: Español rioplatense
Los textos MUST estar en español rioplatense con voseo ("si sos", "mirá", "tenés"), sin tecnicismos sin explicar: cada término del glosario usado en un texto MUST enlazar o remitir a su entrada.

#### Scenario: Término técnico con remisión
- **GIVEN** un texto web que menciona NDVI
- **WHEN** se genera
- **THEN** la primera mención incluye la remisión a la entrada `ndvi` del glosario

### Requirement: Formato numérico argentino
Todo número en texto MUST usar coma decimal y punto de miles, con decimales fijos por unidad según una tabla única (por ejemplo USD/ha sin decimales, mm sin decimales, NDVI con 2, °C con 1, % con 1), redondeo half-up sobre el valor canónico, años sin separador de miles y signo menos ASCII.

#### Scenario: Margen con miles
- **WHEN** se formatea un valor de 1234.5 USD/ha
- **THEN** el texto es "1.235 USD/ha"

#### Scenario: NDVI con decimales
- **WHEN** se formatea un NDVI de 0.675
- **THEN** el texto es "0,68"

#### Scenario: Año sin separador
- **WHEN** se formatea el año 2008 de un escenario
- **THEN** el texto es "2008"

#### Scenario: Ida y vuelta del parser
- **GIVEN** cualquier valor formateado por la tabla
- **WHEN** el parser de formato argentino lo lee
- **THEN** obtiene el valor redondeado que se mostró

### Requirement: Glosario en lenguaje simple
El sistema MUST proveer un glosario versionado con al menos: evapotranspiración, NDVI, anomalía de humedad, balance hídrico, heladas, estrés térmico, GRACE-FO y agua subterránea, y dato satelital vs medición de campo. Cada entrada MUST tener id estable, término, definición corta (para WhatsApp), definición larga (web) y datasets relacionados.

#### Scenario: Glosario completo
- **WHEN** se carga el glosario
- **THEN** contiene las entradas `evapotranspiration`, `ndvi`, `soil_moisture_anomaly`, `water_balance`, `frost`, `heat_stress`, `grace_fo_groundwater` y `satellite_vs_field` con todos los campos completos

#### Scenario: Definición corta para WhatsApp
- **WHEN** se valida cada definición corta
- **THEN** ninguna supera el límite de caracteres de un mensaje WhatsApp

### Requirement: Dato satelital vs medición de campo
La entrada `satellite_vs_field` MUST explicar resolución espacial, la diferencia entre un píxel y un lote, la diferencia entre un sensor remoto o modelo y una muestra de campo, y cómo combinarlos mejora la precisión (el satélite da serie larga y contexto, el campo corrige la escala del lote). Las resoluciones MUST tomarse del catálogo de datasets.

#### Scenario: Combinar satélite y campo
- **WHEN** se renderiza la entrada `satellite_vs_field`
- **THEN** incluye un párrafo sobre cómo combinar datos satelitales y mediciones de campo (pluviómetro, napa, martillador) mejora la precisión, sin cifras inventadas

#### Scenario: Resolución desde el catálogo
- **GIVEN** que el catálogo de datasets declara la resolución de SMAP L4
- **WHEN** se renderiza la entrada `satellite_vs_field`
- **THEN** la resolución mostrada es la del catálogo, formateada en formato argentino

### Requirement: Formato estructurado
La explicación estructurada MUST ser un modelo validado serializable en JSON canónico que incluya `input_hash`, `engine_version`, versión de plantillas, resumen, secciones por rotación, citas, supuestos usados y leyendas.

#### Scenario: Hash de entrada propagado
- **GIVEN** una salida del motor con `input_hash` h
- **WHEN** se genera la explicación estructurada
- **THEN** su campo `input_hash` es h y su campo `templates_version` no está vacío

### Requirement: Texto largo web
El texto web MUST contener resumen comparativo, secciones por rotación, sección propietario vs arrendatario cuando aplique, supuestos usados y leyendas, en texto con marcado mínimo (títulos y listas) sin HTML embebido.

#### Scenario: Sin HTML embebido
- **WHEN** se genera el texto web de una salida de fixture
- **THEN** el texto no contiene etiquetas HTML

### Requirement: Texto corto WhatsApp con partición determinista
El texto WhatsApp MUST resumir posición de la rotación actual, las primeras rotaciones del ranking y su factibilidad. Si supera el límite configurado por mensaje (por defecto 1600 caracteres), MUST dividirse por párrafo, luego por línea y luego por palabra, sin cortar números ni citas, y numerarse "(n/m)".

#### Scenario: Texto que entra en un mensaje
- **GIVEN** un resumen de 900 caracteres
- **WHEN** se particiona con límite 1600
- **THEN** se produce un solo mensaje sin marcador de partición

#### Scenario: Texto largo partido
- **GIVEN** un detalle de 3500 caracteres
- **WHEN** se particiona con límite 1600
- **THEN** se producen mensajes de a lo sumo 1600 caracteres cada uno, marcador incluido, numerados (1/3), (2/3), (3/3), cuya concatenación sin marcadores reproduce el texto original salvo los espacios en blanco de los puntos de corte

#### Scenario: Partición estable
- **GIVEN** el mismo texto y el mismo límite
- **WHEN** se particiona dos veces
- **THEN** los cortes caen en las mismas posiciones

### Requirement: Incertidumbre entre años secos y húmedos
Para cada rotación con economía completa, la explicación MUST mostrar el rango de margen por clase anual (mínimo, esperado y máximo de DRY, NORMAL y WET) del resultado y el rango hídrico por clase de water-feasibility, citando cada número, y MUST decir que la dispersión entre años es la forma en que la herramienta expresa la incertidumbre.

#### Scenario: Rango de margen citado
- **GIVEN** una rotación con rango DRY 100 a 150 USD/ha y WET 500 a 600 USD/ha en la salida
- **WHEN** se genera el texto web
- **THEN** el texto menciona ambos rangos con sus citas y no solo el margen esperado

#### Scenario: Rango hídrico citado
- **GIVEN** un rango de agua a la siembra de la soja de segunda por clase en la salida
- **WHEN** se genera el texto web
- **THEN** el texto contrasta años secos y húmedos con esos valores citados

#### Scenario: Clase vacía
- **WHEN** el rango WET viene vacío
- **THEN** el texto dice con una frase fija que no hubo años húmedos válidos, sin inventar valores

### Requirement: Riesgo explicado como cola de márgenes
El texto del término de riesgo MUST explicar el Riesgo como el faltante del margen en la cola de peso q de los años históricos (A-ACT-05) frente al margen medio, citando el valor del resultado, y MUST NOT describirlo como el margen de los años de clase DRY.

#### Scenario: Riesgo con su definición
- **WHEN** se explica una rotación con término de riesgo dominante
- **THEN** el texto habla de "los peores años del registro" con la marca de supuesto A-ACT-05 y no menciona la clase DRY como definición del riesgo

### Requirement: Calendarios explicados
La explicación MUST describir el calendario de suelo desnudo de cada rotación por tramos de meses y, para la actual, la fracción observada de NDVI bajo umbral como evidencia OBSERVED; y el calendario de vulnerabilidad por cultivo con los meses de nivel MEDIUM o HIGH por evento (helada y déficit en P0, calor y lluvia extrema en P1), todo citado desde la salida.

#### Scenario: Invierno desnudo en soja continua
- **GIVEN** soja continua con días sin cultivo vivo de junio a septiembre en la salida
- **WHEN** se genera el texto web
- **THEN** el texto dice en qué meses el lote queda sin cultivo vivo, cita los días por mes y la evidencia NDVI observada del lote

#### Scenario: Vulnerabilidad por mes
- **GIVEN** un calendario con déficit HIGH en enero para la soja de segunda
- **WHEN** se genera el texto web
- **THEN** el texto menciona enero, el cultivo, el evento y la frecuencia citada

#### Scenario: Calendario sin meses vulnerables
- **WHEN** ningún mes supera el nivel LOW
- **THEN** el texto usa una frase fija de "sin meses con vulnerabilidad media o alta registrada"

### Requirement: Años con pérdida y margen en un año malo
Para cada rotación con economía completa, la explicación MUST decir en cuántos de los N años reales del registro el margen anual fue negativo, cuáles fueron, y el margen del peor año con su año, citando los campos del resultado del motor. MUST aclarar que es margen bruto y si incluye arrendamiento.

#### Scenario: Pérdida en años reales
- **GIVEN** un resultado con 4 de 30 años con pérdida y peor año 2008 con −120 USD/ha (ejemplo)
- **WHEN** se genera el texto web
- **THEN** el texto dice "en 4 de los 30 años reales habrías perdido plata" y "en el peor año (2008) el margen fue de −120 USD/ha", con citas a los campos del resultado

#### Scenario: Sin años con pérdida
- **WHEN** el resultado informa 0 años con pérdida
- **THEN** el texto usa una frase fija con el 0 citado y el margen del peor año citado

### Requirement: Lluvia sobre suelo desnudo explicada
La explicación MUST informar, por rotación, los mm de lluvia caídos en promedio sobre suelo desnudo y los meses que más aportan, citados desde el resultado, como proxy de riesgo de erosión, y MUST compararlos de forma cualitativa con la rotación actual.

#### Scenario: Servicio contra soja continua
- **GIVEN** resultados de soja continua y de soja con centeno con su lluvia sobre suelo desnudo
- **WHEN** se genera el texto web de la rotación con centeno
- **THEN** el texto cita los mm de ambas desde el resultado y dice que con el servicio cae menos lluvia sobre suelo desnudo, sin calcular la diferencia

### Requirement: Tres miradas deterministas
En P1 la explicación de cada rotación MUST agrupar su contenido, sin cambiar las cinco secciones, en tres miradas fijas por plantilla: clima (escenarios, helada, calor, lluvia extrema, POWER vs IMERG), suelo y agua (factibilidad, agua a la siembra, ΔSuelo, suelo desnudo) y economía (VAN, Riesgo, años con pérdida, capital). MUST NOT usar LLM ni números nuevos.

#### Scenario: Miradas completas
- **WHEN** se genera la explicación estructurada de una rotación
- **THEN** trae `lenses` con `climate`, `soil_water` y `economics` en ese orden, cada una con sus citas, y las cinco secciones siguen presentes

#### Scenario: Mirada sin contenido
- **WHEN** una rotación no tiene riesgos climáticos de nivel MEDIUM o HIGH
- **THEN** la mirada de clima usa una frase fija y no se omite

### Requirement: Robustez del ranking explicada
En P1, cuando la aplicación provea la robustez, la explicación MUST decir en cuántas clases de año y en cuántos de los 4 perfiles predefinidos la rotación sale primera, citando los conteos, y MUST NOT traducirlos a porcentaje ni a probabilidad.

#### Scenario: Robustez citada
- **GIVEN** una rotación primera en 2 de 3 clases y 3 de 4 perfiles (ejemplo)
- **WHEN** se genera el texto web
- **THEN** el texto dice "sale primera en 2 de 3 tipos de año y para 3 de 4 actores" con citas y sin porcentajes

### Requirement: Lluvia POWER vs IMERG en la evidencia
En P1, cuando la entrada traiga la comparación de lluvia por año, la evidencia MUST mostrar los años con discrepancia (A-CLI-04) con ambas sumas citadas y la frase fija "para el balance de agua tomamos la más conservadora (la menor)" con la marca A-WAT-16, y MUST aclarar que los tipos de año se clasifican solo con POWER.

#### Scenario: Discrepancia contada
- **GIVEN** la campaña 2015 con 600 mm POWER y 420 mm IMERG (ejemplo)
- **WHEN** se genera la evidencia
- **THEN** el texto cita ambas cifras, dice que el balance usó IMERG por ser la menor y marca A-WAT-16

### Requirement: Orden de presentación sin tocar el ranking
Cuando la aplicación provea un orden de presentación por preferencias del productor, los resúmenes MUST listar las rotaciones en ese orden mostrando siempre el rango del motor de cada una, y MUST decir en una frase fija qué preferencia se aplicó. El texto MUST NOT afirmar que el orden mostrado es el ranking.

#### Scenario: Primero las no riesgosas en agua
- **GIVEN** un orden de presentación que pone primero las rotaciones FEASIBLE
- **WHEN** se genera el resumen WhatsApp
- **THEN** las rotaciones aparecen en ese orden, cada una con "puesto N del ranking" citado, y una línea dice "mostramos primero las que no son riesgosas en agua"

### Requirement: Ficha exportable por rotación
En P2 el sistema MUST generar por rotación una ficha para banco o certificadora con: lote, rotación, actor y horizonte, Riesgo, años con pérdida y peor año, factibilidad hídrica con motivos, ΔSuelo con componentes, lluvia sobre suelo desnudo, supuestos con estado, `input_hash`, `engine_version` y las leyendas, todo citado con procedencia, en JSON canónico y texto con marcado mínimo.

#### Scenario: Ficha completa y trazable
- **WHEN** se genera la ficha de R_MAIZE_SOY_COVER del lote demo
- **THEN** cada número tiene cita con procedencia, la ficha trae `input_hash` y `engine_version`, y el test de trazabilidad pasa sobre su texto

#### Scenario: Ficha con factibilidad desconocida
- **WHEN** la rotación tiene factibilidad UNKNOWN
- **THEN** la ficha dice "desconocida" con el faltante y no la presenta como no apta
