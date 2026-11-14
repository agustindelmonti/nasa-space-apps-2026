# Spec Delta

## Purpose

Convierte series diarias de lluvia del registro NASA en conjuntos deterministas de escenarios climáticos históricos (año, clase seco/normal/húmedo, lluvia de ventana y peso) para que el motor calcule esperanza y riesgo sobre años reales enumerados.

## ADDED Requirements

### Requirement: Ventanas de campaña configurables
El sistema MUST clasificar por separado dos ventanas de campaña definidas por el supuesto A-CLI-01 (ejemplo: invierno 1 de mayo a 31 de octubre del año Y; verano 1 de noviembre del año Y a 31 de marzo del año Y+1). Cada escenario MUST identificarse por el año de inicio de la campaña. Las ventanas MUST leerse del registro de supuestos, no estar fijas en el código.

#### Scenario: Verano que cruza el año calendario
- **GIVEN** la ventana de verano del ejemplo de A-CLI-01
- **WHEN** se clasifica la campaña que empieza en 2008
- **THEN** la lluvia considerada va del 2008-11-01 al 2009-03-31 y el escenario se identifica como año 2008

#### Scenario: Ventana cambiada por agrónomos
- **GIVEN** que A-CLI-01 se edita para que el invierno termine el 30 de septiembre
- **WHEN** se vuelve a clasificar
- **THEN** los acumulados de invierno usan la nueva fecha sin cambios de código y la salida cita A-CLI-01

### Requirement: Lluvia de ventana desde fuente declarada
La lluvia de ventana MUST ser el acumulado de la precipitación diaria de una única fuente declarada por clasificación (NASA_POWER PRECTOTCORR por defecto, por su cobertura desde 1981), emitido como PValue DERIVED en mm con `derived_from` y método. El sistema MUST NOT mezclar fuentes dentro de una misma clasificación.

#### Scenario: Fuente única
- **WHEN** se clasifican años con POWER como fuente
- **THEN** todos los escenarios citan `NASA_POWER` / `PRECTOTCORR` en su procedencia y ninguno cita IMERG

#### Scenario: Fuentes mezcladas rechazadas
- **WHEN** la serie de entrada contiene días de POWER y días de IMERG para la misma clasificación
- **THEN** la clasificación falla con el error tipado `MIXED_SOURCES`

### Requirement: Exclusión de años incompletos con registro
Un año MUST excluirse de la clasificación de una ventana si la cantidad de días faltantes en esa ventana supera la tolerancia A-CLI-02, o si la ventana no terminó dentro del período de la serie. Cada exclusión MUST quedar registrada con año, ventana, motivo (`MISSING_DAYS` o `INCOMPLETE_WINDOW`) y cantidad de días faltantes. Los días faltantes MUST NOT rellenarse.

#### Scenario: Año con huecos excluido
- **GIVEN** A-CLI-02 con tolerancia de ejemplo 0 días faltantes
- **WHEN** la ventana de invierno de 1995 tiene 3 días faltantes
- **THEN** 1995 no aparece en los escenarios de invierno y el registro de exclusiones dice `MISSING_DAYS` con 3 días

#### Scenario: Campaña en curso excluida
- **GIVEN** una serie que termina el 2026-11-10
- **WHEN** se clasifica la ventana de verano
- **THEN** la campaña 2026 se excluye con motivo `INCOMPLETE_WINDOW`

#### Scenario: Año bisiesto
- **WHEN** la ventana de verano de la campaña 2007 incluye el 2008-02-29
- **THEN** la ventana espera 152 días y el 29 de febrero cuenta como un día más, no como faltante ni excedente

### Requirement: Mínimo de años para clasificar
El sistema MUST exigir al menos A-CLI-03 años válidos (ejemplo: 15) en una ventana para clasificarla. Con menos años válidos, MUST devolver el error tipado `INSUFFICIENT_YEARS` con la cantidad disponible y la requerida, y MUST NOT emitir clases parciales.

#### Scenario: Pocos años
- **GIVEN** A-CLI-03 con valor de ejemplo 15
- **WHEN** solo hay 12 años válidos para la ventana de invierno
- **THEN** la clasificación de invierno falla con `INSUFFICIENT_YEARS` (12 de 15) y no se emiten escenarios de invierno

### Requirement: Clasificación por terciles con desempate documentado
Con N años válidos, el sistema MUST ordenar los años por lluvia de ventana redondeada a 0.1 mm ascendente y, a igualdad, por año ascendente. Los primeros floor(N/3) MUST ser DRY, los últimos floor(N/3) WET y el resto NORMAL. Los límites de tercil MUST informarse como DERIVED.

#### Scenario: N divisible por 3
- **GIVEN** 30 años válidos con lluvias distintas
- **WHEN** se clasifican
- **THEN** hay 10 DRY, 10 NORMAL y 10 WET, y los 10 de menor lluvia son DRY

#### Scenario: Resto asignado a NORMAL
- **GIVEN** 31 años válidos
- **WHEN** se clasifican
- **THEN** hay 10 DRY, 11 NORMAL y 10 WET

#### Scenario: Empate en el límite de tercil
- **GIVEN** 30 años donde 2003 y 2011 tienen la misma lluvia redondeada y ocupan las posiciones 10 y 11
- **WHEN** se clasifican
- **THEN** 2003 queda DRY y 2011 queda NORMAL, y el resultado lista ese empate en `tie_breaks`

#### Scenario: Ruido de punto flotante
- **WHEN** dos años tienen 412.04999999 mm y 412.05 mm
- **THEN** ambos se comparan como 412.1 mm y el orden entre ellos lo decide el año

### Requirement: Pesos uniformes por año
Cada escenario de una ventana MUST tener peso 1/N, con N la cantidad de años válidos de esa ventana, y la suma de pesos MUST ser 1 con la tolerancia de `domain-models`. El resultado MUST informar la frecuencia empírica de cada clase. Los pesos MUST tener procedencia DERIVED con método `uniform_1_over_n`.

#### Scenario: Pesos de 31 años
- **WHEN** se clasifican 31 años válidos
- **THEN** cada escenario pesa 1/31, la suma es 1 dentro de 1e-9, y la frecuencia DRY informada es 10/31

### Requirement: Resultado trazable de la clasificación
La salida por ventana MUST incluir: ventana usada con su assumption_id, fuente, lista ordenada por año de escenarios (año, clase, lluvia en mm, peso), límites de tercil, años excluidos con motivo, empates resueltos, supuestos usados y versión del método. La lista de escenarios MUST ordenarse por año ascendente.

#### Scenario: Salida completa
- **WHEN** se clasifica la ventana de verano del lote de demo
- **THEN** la salida contiene escenarios ordenados por año, límites de tercil DERIVED, la lista de excluidos (vacía o no) y los ids A-CLI-01, A-CLI-02 y A-CLI-03

### Requirement: Clasificación determinista y pura
La clasificación MUST ser una función pura: sin red, sin reloj, sin aleatoriedad y sin lectura de archivos. La misma entrada MUST producir la misma salida serializada canónicamente, byte a byte, independientemente del orden en que lleguen los días de la serie.

#### Scenario: Orden de entrada irrelevante
- **GIVEN** una serie diaria y la misma serie con los días permutados
- **WHEN** se clasifican ambas
- **THEN** las salidas canónicas son idénticas byte a byte

#### Scenario: Sin red
- **WHEN** se ejecuta la clasificación con la red bloqueada
- **THEN** termina con el mismo resultado que con red disponible

### Requirement: Cruce con GPM IMERG como advertencia
Si se provee lluvia IMERG para los años en común (desde 2000), el sistema MUST calcular por año la diferencia relativa de lluvia de ventana entre POWER e IMERG y MUST emitir una advertencia por cada año que supere el umbral A-CLI-04 (ejemplo: 25 %). El cruce MUST NOT cambiar clases, pesos ni años incluidos.

#### Scenario: Discrepancia advertida
- **GIVEN** A-CLI-04 con valor de ejemplo 25 %
- **WHEN** en el verano 2015 POWER acumula 600 mm e IMERG 420 mm
- **THEN** la salida incluye una advertencia para 2015 con ambas cifras y la clase de 2015 es la misma que sin IMERG

#### Scenario: Regla conservadora del balance no reclasifica
- **GIVEN** que water-feasibility usa IMERG para el balance de 2015 por la regla A-WAT-16
- **WHEN** se clasifican los años
- **THEN** la clase de 2015 sale solo de POWER y la salida no cita IMERG como fuente de clasificación

#### Scenario: Sin IMERG
- **WHEN** no se provee IMERG
- **THEN** la clasificación es idéntica y el resultado indica que el cruce no se realizó

### Requirement: Clase anual y escenario combinado por año
El sistema MUST armar un EscenarioClimático por año válido en ambas ventanas, con clase de invierno, clase de verano y clase anual. La clase anual MUST salir de terciles, con la misma regla de orden y desempate, de la lluvia de campaña (suma de ambas ventanas) sobre esos años. Cada escenario combinado MUST pesar 1/N con N los años del conjunto combinado.

#### Scenario: Tres clases por año
- **GIVEN** 30 años válidos en invierno y en verano
- **WHEN** se arman los escenarios combinados
- **THEN** cada año trae clase de invierno, de verano y anual, hay 10 años DRY anuales y cada peso es 1/30

#### Scenario: Año válido en una sola ventana
- **WHEN** 1995 se excluye en invierno por `MISSING_DAYS` y es válido en verano
- **THEN** 1995 no forma parte de los escenarios combinados y el registro de exclusiones lo explica

#### Scenario: Clases independientes
- **WHEN** un año es DRY en invierno y WET en verano
- **THEN** su clase anual se calcula con la lluvia de campaña y puede ser cualquiera de las tres

### Requirement: Chequeo de consistencia con rindes MAGyP
En P1 el sistema MUST ofrecer un reporte que, para el departamento del lote demo, contraste cada año DRY anual con el rinde departamental de soja y maíz de MAGyP (Estimaciones Agrícolas) según A-CLI-11, informando por año si es consistente, inconsistente o sin dato. El reporte MUST citar fuente y fecha y MUST NOT alimentar al motor ni cambiar clases.

#### Scenario: Año seco con caída de rinde
- **GIVEN** 2008 DRY anual y un rinde departamental de soja 2008/09 en el tercio inferior del período comparado (ejemplo)
- **WHEN** se arma el reporte
- **THEN** 2008 figura como consistente, con el rinde citado con fuente MAGyP y fecha de descarga, y A-CLI-11

#### Scenario: Año sin rinde publicado
- **WHEN** MAGyP no publica rinde departamental para una campaña
- **THEN** el año figura sin dato y no se completa con otro departamento

#### Scenario: Validación fuera del motor
- **WHEN** se agrega o quita el archivo de rindes MAGyP
- **THEN** los escenarios, el `input_hash` y la salida del motor no cambian

### Requirement: Comparación de enfoques estadísticos
Como chequeo (P2) que no alimenta al motor, el sistema MUST poder agrupar los años con un método de agrupamiento determinista (semilla fija documentada) sobre lluvia de ventana, ET0 y días con helada, y MUST reportar la coincidencia con la clasificación por terciles (años en la misma clase y años que cambian), para explicar por qué el motor usa terciles.

#### Scenario: Reporte de coincidencia
- **GIVEN** la serie POWER del lote demo
- **WHEN** se corre la comparación
- **THEN** el reporte lista cuántos años coinciden entre ambos métodos y cuáles cambian de clase, y dos corridas dan el mismo resultado
