# Spec Delta

## Purpose

Obtiene, valida y cachea por punto los datasets NASA que usa la herramienta (POWER, SMAP L4, GPM IMERG, GRACE/GRACE-FO, MODIS/HLS NDVI, SRTM) y las propiedades de suelo de SoilGrids, con procedencia completa, huecos explícitos y metadatos de resolución y limitación, para que la aplicación arme entradas del motor sin red y sin datos inventados.

## ADDED Requirements

### Requirement: Ingesta diaria de NASA POWER por punto
El sistema MUST obtener series diarias de NASA POWER para un punto (lat/lon) y un período con inicio no anterior a 1981-01-01, usando el endpoint diario por punto de la comunidad AG. MUST incluir al menos PRECTOTCORR (mm/día), T2M, T2M_MIN, T2M_MAX (°C), RH2M (%), WS2M (m/s) y ALLSKY_SFC_SW_DWN (MJ/m²/día), más los insumos que requiera ET0 (ver requisito de ET0).

#### Scenario: Serie POWER del lote de demo
- **GIVEN** el punto del lote `demo-casilda` y el período 1981-01-01 a 2025-12-31
- **WHEN** se ingesta NASA POWER
- **THEN** la serie tiene una fila por día del período con las variables requeridas en columnas con unidad declarada
- **AND** cada variable tiene metadatos con `dataset=NASA_POWER`, su nombre de parámetro POWER y la resolución de la grilla de origen

#### Scenario: Período anterior a 1981 rechazado
- **WHEN** se pide POWER con inicio 1975-01-01
- **THEN** la ingesta falla con un error tipado `PERIOD_OUT_OF_COVERAGE` que indica la cobertura disponible

#### Scenario: Variable con cobertura más corta
- **GIVEN** que la radiación solar de POWER empieza después que la meteorología
- **WHEN** se ingesta un período que arranca en 1981
- **THEN** los días sin radiación quedan registrados como faltantes de ALLSKY_SFC_SW_DWN y no se rellenan

### Requirement: Evapotranspiración de referencia trazable
El sistema MUST entregar ET0 diaria (mm/día) para el punto. Si POWER ofrece un parámetro de ET de referencia FAO-56, MUST usarlo como OBSERVED con su Source. Si no, MUST calcularla con FAO-56 Penman-Monteith a partir de variables POWER y marcarla DERIVED con `derived_from` y método. Un día con algún insumo faltante MUST dar ET0 faltante.

#### Scenario: ET0 calculada con Penman-Monteith
- **GIVEN** que POWER no ofrece ET0 FAO-56 directa
- **WHEN** se ingesta un día con T2M_MAX, T2M_MIN, RH2M, WS2M, ALLSKY_SFC_SW_DWN y presión superficial completos
- **THEN** la ET0 del día es DERIVED, lista esas variables en `derived_from` y declara el método `FAO56_PENMAN_MONTEITH`

#### Scenario: ET0 con insumo faltante
- **WHEN** un día no tiene ALLSKY_SFC_SW_DWN
- **THEN** la ET0 de ese día queda faltante y el día aparece en el registro de huecos de ET0

### Requirement: Ingesta de humedad de zona de raíces SMAP L4
El sistema MUST obtener del producto SMAP L4 SPL4SMGP la variable `sm_rootzone` (m³/m³, 0 a 100 cm) para la celda de ~9 km que contiene el punto, desde 2015-03-31. Los valores 3-horarios MUST conservarse en caché y la media diaria MUST ser DERIVED. La fuente MUST declarar `is_modeled=true` (asimilación en modelo de superficie).

#### Scenario: Media diaria desde 3-horario
- **GIVEN** un día con los 8 valores 3-horarios de `sm_rootzone` disponibles
- **WHEN** se calcula la humedad diaria
- **THEN** el valor es DERIVED, con método `daily_mean_of_3h` y `derived_from` apuntando a la serie 3-horaria

#### Scenario: Día SMAP incompleto
- **WHEN** un día tiene 5 de 8 valores 3-horarios
- **THEN** la media diaria queda faltante y el registro de huecos indica 3 pasos ausentes, sin promediar los disponibles

#### Scenario: Pedido anterior a SMAP
- **WHEN** se pide SMAP L4 para 2010
- **THEN** la ingesta falla con `PERIOD_OUT_OF_COVERAGE` indicando inicio 2015-03-31

### Requirement: Ingesta de precipitación GPM IMERG
El sistema MUST obtener precipitación diaria (mm/día) de GPM IMERG Final Run diario para la celda de ~0.1° que contiene el punto, dentro de la cobertura de la versión usada (desde 2000-06 o antes según versión). La versión del producto MUST quedar en la Source. IMERG MUST servir como cruce de la lluvia de POWER, no como reemplazo silencioso.

#### Scenario: Serie IMERG con versión
- **WHEN** se ingesta IMERG para 2001 a 2024
- **THEN** cada registro tiene `dataset=GPM_IMERG`, variable de precipitación, versión del producto y resolución 0.1° diaria

#### Scenario: Latencia del Final Run
- **WHEN** se pide IMERG Final Run para un mes todavía no publicado
- **THEN** los días no publicados quedan registrados como faltantes con motivo `NOT_YET_PUBLISHED`

### Requirement: Ingesta de anomalía de almacenamiento de agua GRACE/GRACE-FO
El sistema MUST obtener la anomalía mensual de almacenamiento terrestre de agua (TWS, cm de equivalente de agua) de una solución mascon (JPL o CSR) para la celda que contiene el punto, uniendo GRACE y GRACE-FO. La Source MUST declarar la solución, la línea base de la anomalía y resolución efectiva aproximada de 300 km.

#### Scenario: Hueco entre misiones
- **WHEN** se ingesta TWS de 2016 a 2019
- **THEN** los meses entre el fin de GRACE (2017) y el inicio de GRACE-FO (2018) aparecen como faltantes con motivo `MISSION_GAP` y no se interpolan

#### Scenario: Resolución efectiva declarada
- **WHEN** se consulta la metadata de la serie TWS
- **THEN** indica resolución efectiva ~300 km y la limitación "dato regional, no describe un lote individual"

### Requirement: Ingesta de NDVI MODIS y HLS
El sistema MUST obtener NDVI de MODIS MOD13Q1 (250 m, compuestos de 16 días, desde 2000) para el píxel que contiene el punto, aplicando la escala del producto y descartando píxeles con calidad no confiable según su capa QA. HLS (30 m) MUST seguir el mismo contrato si se implementa, con NDVI DERIVED desde bandas roja e infrarroja.

#### Scenario: Píxel nublado
- **WHEN** un compuesto MOD13Q1 tiene calidad "nube" en la capa QA para el píxel
- **THEN** el NDVI de ese compuesto queda faltante con motivo `QA_REJECTED`

#### Scenario: Escala aplicada
- **WHEN** el valor crudo de NDVI es 7500
- **THEN** el valor guardado es 0.75 adimensional

### Requirement: Catálogo de metadatos por dataset
El sistema MUST exponer, por dataset, un registro con nombre, producto y versión, variables, resolución espacial y temporal, cobertura temporal, latencia típica, si es modelado y una limitación en lenguaje simple. La aplicación y la web MUST poder leer este catálogo sin red.

#### Scenario: Consulta de limitaciones
- **WHEN** la web pide el catálogo de datasets
- **THEN** recibe una entrada por dataset (NASA_POWER, SMAP_L4, GPM_IMERG, GRACE_FO, MODIS_NDVI, y SOILGRIDS, SRTM y HLS_NDVI si están habilitados) con resolución y limitación no vacías

### Requirement: Procedencia completa por registro
Cada valor ingestado MUST llevar una Source completa según `domain-models`: dataset, variable, período, resolución espacial y temporal, `is_modeled`, versión del producto y coordenadas de la celda o píxel efectivamente usado. Un valor sin Source completa MUST NOT salir de la capa de datos.

#### Scenario: Celda efectiva registrada
- **GIVEN** un punto que cae dentro de una celda POWER cuyo centro no coincide con el punto
- **WHEN** se arma la Source
- **THEN** la Source incluye tanto las coordenadas pedidas como las de la celda de origen

#### Scenario: Source incompleta bloqueada
- **WHEN** un adaptador intenta devolver un valor sin resolución temporal
- **THEN** la capa de datos falla con un error tipado en lugar de entregar el valor

### Requirement: Huecos explícitos sin interpolación
El sistema MUST convertir valores de relleno del producto (por ejemplo -999 en POWER) y datos ausentes en faltantes explícitos, y MUST registrar cada hueco con dataset, variable, fecha o paso, y motivo. El sistema MUST NOT interpolar, rellenar con climatología ni sustituir con otro dataset en silencio.

#### Scenario: Valor de relleno de POWER
- **WHEN** POWER devuelve -999 en PRECTOTCORR para un día
- **THEN** ese día queda faltante con motivo `FILL_VALUE` y no aparece como 0 ni como -999

#### Scenario: Reporte de huecos
- **WHEN** se termina una ingesta con faltantes
- **THEN** el resultado incluye un reporte con la cantidad de faltantes por variable y la lista de fechas o pasos afectados

### Requirement: Caché parquet validada por esquema
Cada ingesta MUST persistirse en `data/cache/<dataset>/<lat>_<lon>_<period>.parquet` con metadatos de la consulta (parámetros, versión, fecha de descarga, hash del contenido). Toda lectura y escritura de caché MUST validar el esquema del dataset (columnas, tipos, unidades, rangos físicos); un archivo inválido MUST rechazarse con error tipado.

#### Scenario: Caché corrupta
- **GIVEN** un parquet de POWER con la columna T2M_MAX ausente
- **WHEN** se lee desde caché
- **THEN** la lectura falla con `CACHE_SCHEMA_INVALID` nombrando la columna faltante

#### Scenario: Rango físico fuera de lo plausible
- **WHEN** una fila de SMAP tiene `sm_rootzone` = 1.7 m³/m³
- **THEN** la validación de esquema falla indicando el rango permitido

### Requirement: Ingesta idempotente
Repetir una ingesta con el mismo dataset, punto, período y versión MUST NOT volver a descargar si la caché es válida, y MUST producir un contenido de caché idéntico (mismo hash de contenido). Las coordenadas MUST normalizarse con una precisión fija antes de formar la clave de caché.

#### Scenario: Segunda ingesta sin red
- **GIVEN** una ingesta exitosa de POWER para el lote de demo
- **WHEN** se repite la misma ingesta
- **THEN** no se hace ninguna llamada de red y el hash del contenido es el mismo

#### Scenario: Coordenadas equivalentes
- **WHEN** se pide el mismo dataset para lat -33.04400001 y lat -33.044
- **THEN** ambas consultas usan la misma clave de caché

### Requirement: Funcionamiento offline desde caché
Con modo offline activo (`DEMO_MODE=1` u `OFFLINE=1`), el sistema MUST leer solo caché y fixtures y MUST NOT abrir conexiones de red. Si el dato pedido no está en caché, MUST fallar con `DATA_NOT_CACHED` indicando dataset, punto y período.

#### Scenario: Demo sin internet
- **GIVEN** `DEMO_MODE=1` y los fixtures de `demo-casilda` presentes
- **WHEN** la aplicación pide el contexto NASA del lote
- **THEN** obtiene todas las series desde caché sin intentos de red

#### Scenario: Faltante en modo offline
- **WHEN** en modo offline se pide un punto sin caché
- **THEN** la respuesta es `DATA_NOT_CACHED` y no hay intento de red

### Requirement: Credenciales Earthdata por entorno
Las credenciales de NASA Earthdata MUST leerse de variables de entorno o `.env` (`EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`, o `EARTHDATA_TOKEN`). El repo MUST incluir `.env.example` sin valores reales. Las credenciales MUST NOT aparecer en logs, caché ni respuestas. POWER MUST funcionar sin credenciales.

#### Scenario: Falta de credenciales
- **GIVEN** que no hay credenciales Earthdata configuradas y no hay modo offline
- **WHEN** se pide SMAP L4 sin caché
- **THEN** la ingesta falla con `EARTHDATA_AUTH_MISSING` y POWER sigue disponible

#### Scenario: Secretos fuera de logs
- **WHEN** se ejecuta una ingesta autenticada con logging en nivel DEBUG
- **THEN** ningún log contiene el valor de la contraseña ni del token

### Requirement: Agregaciones como valores derivados
Las agregaciones (media diaria desde 3-horario, acumulado de lluvia por ventana, total anual, media o máximo de NDVI por ventana, anomalía TWS de un mes) MUST emitirse como PValue DERIVED con `derived_from`, método y conteo de pasos usados y faltantes. Una agregación con faltantes MUST marcarse incompleta y no completarse.

#### Scenario: Acumulado de ventana con huecos
- **GIVEN** una ventana de 184 días con 2 días faltantes de PRECTOTCORR
- **WHEN** se calcula el acumulado de lluvia de la ventana
- **THEN** el resultado es DERIVED, informa 182 días usados y 2 faltantes, y está marcado incompleto

#### Scenario: Acumulado completo
- **WHEN** la ventana no tiene faltantes
- **THEN** el acumulado está marcado completo y su método es `sum_daily`

### Requirement: Contexto de relieve desde SRTM
El sistema MUST obtener la elevación SRTM (30 m) en una ventana fija alrededor del lote y derivar la pendiente media (%) y la posición relativa del lote en el relieve (LOMA, MEDIA_LOMA, BAJO) como DERIVED con Source SRTM, para usarlas solo como evidencia de anegamiento y erosión. Estos valores MUST NOT ser insumo del motor.

#### Scenario: Lote en un bajo
- **GIVEN** una ventana SRTM donde la elevación del lote está en el tercio inferior de la ventana
- **WHEN** se calcula el contexto de relieve
- **THEN** la posición es BAJO, DERIVED con `derived_from` la elevación SRTM, y la evidencia menciona riesgo de anegamiento a revisar localmente

#### Scenario: Relieve fuera del motor
- **WHEN** se arma `EngineInput` para un lote con contexto SRTM
- **THEN** la entrada no contiene pendiente ni posición y el `input_hash` no cambia por el contexto SRTM

### Requirement: Evidencia de estrés desde ECOSTRESS
El sistema MUST poder obtener (P2) LST y ET de ECOSTRESS para fechas con pasada sobre el lote, como OBSERVED con Source ECOSTRESS, fecha y hora de pasada, solo para el panel de evidencia. Estos valores MUST NOT ser insumo del motor y la falta de pasadas MUST quedar registrada como hueco.

#### Scenario: Pasada con nubes
- **WHEN** la pasada de una fecha está marcada como nublada en la capa de calidad
- **THEN** el valor queda faltante con motivo `QA_REJECTED`

#### Scenario: ECOSTRESS fuera del motor
- **WHEN** se arma `EngineInput`
- **THEN** no contiene valores de ECOSTRESS

### Requirement: Muestreo al lote sin re-grillado
Cada dataset MUST muestrearse en su resolución nativa al elemento (celda o píxel) que contiene el centroide del lote, o a una ventana fija para SRTM, sin re-grillar ni interpolar a una grilla común en el MVP, y la Source MUST registrar la celda efectiva y su tamaño. El catálogo MUST documentar la regla por dataset.

#### Scenario: Celdas de distinto tamaño
- **WHEN** se arma el contexto del lote demo con POWER, SMAP L4 e IMERG
- **THEN** cada valor cita su propia celda efectiva con su tamaño y ninguno fue interpolado a otra grilla

### Requirement: Resumen NDVI mensual del lote
El sistema MUST derivar de la serie NDVI del píxel del lote un resumen por mes calendario con la mediana de NDVI y la fracción de compuestos válidos bajo el umbral A-SOIL-10, con período, conteo de compuestos usados y faltantes, como DERIVED, para incluirlo en `EngineInput`.

#### Scenario: Mes sin compuestos válidos
- **WHEN** todos los compuestos de julio fueron rechazados por QA
- **THEN** el resumen de julio queda faltante con el conteo de rechazados y no se completa con meses vecinos

### Requirement: Propiedades de suelo desde SoilGrids
En P1 el sistema MUST obtener de la API REST de SoilGrids, para el píxel de 250 m del lote y por capa estándar, textura (arena, limo, arcilla), carbono orgánico y contenido volumétrico de agua a 33 kPa y 1500 kPa, como OBSERVED con `dataset=SOILGRIDS` e `is_modeled=true`, cacheados como los demás datasets. La limitación MUST decir que es un modelo global que no reemplaza la carta de suelo INTA.

#### Scenario: Suelo SoilGrids del lote demo
- **GIVEN** el punto del lote `demo-casilda`
- **WHEN** se ingesta SoilGrids
- **THEN** cada propiedad por capa tiene Source con `dataset=SOILGRIDS`, `is_modeled=true`, resolución 250 m, capa en cm y la limitación frente a la carta INTA

#### Scenario: SoilGrids sin dato
- **WHEN** la API de SoilGrids no devuelve valor para una capa
- **THEN** esa capa queda faltante con motivo `NO_DATA` y no se completa con capas vecinas

### Requirement: Agua útil integrada desde SoilGrids
El sistema MUST derivar el agua útil del perfil (mm) sumando por capa (θ a 33 kPa − θ a 1500 kPa) × espesor hasta la profundidad de A-WAT-17, como DERIVED con `derived_from` las capas SoilGrids y A-WAT-17. Si falta alguna capa dentro de esa profundidad, MUST NOT emitir el valor y MUST registrar el faltante.

#### Scenario: Agua útil por capas
- **GIVEN** capas SoilGrids completas de 0 a 100 cm y A-WAT-17 con profundidad de ejemplo 100 cm
- **WHEN** se integra el agua útil
- **THEN** el valor es DERIVED en mm, cita las cinco capas usadas y A-WAT-17

#### Scenario: Capa faltante
- **WHEN** falta la capa de 30 a 60 cm
- **THEN** no se emite agua útil y el faltante nombra la capa

### Requirement: Comparación de lluvia POWER vs IMERG por campaña
En P1 el sistema MUST derivar, por año de campaña con ambas series completas en el período, la lluvia acumulada POWER PRECTOTCORR y GPM IMERG, su diferencia relativa y cuál es menor, como DERIVED con ambas Source, para el panel de evidencia y para la regla conservadora de water-feasibility. Un año con alguna serie incompleta MUST marcarse sin comparación.

#### Scenario: Comparación de un año
- **GIVEN** la campaña 2015 con 600 mm según POWER y 420 mm según IMERG (ejemplo), ambas completas
- **WHEN** se arma la comparación
- **THEN** informa ambas sumas, la diferencia relativa y que IMERG es la menor, todo DERIVED citando ambas fuentes

#### Scenario: Año anterior a IMERG
- **WHEN** la campaña 1990 no tiene IMERG
- **THEN** la comparación de 1990 queda marcada `NO_IMERG` y no se inventa valor
