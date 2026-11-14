# Spec Delta

## Purpose

Registra lecturas de impacto tomadas con el acelerómetro del celular (martillador tipo Clegg casero), las valida y normaliza de forma relativa y no calibrada, y las muestra junto a la humedad SMAP L4 para explicar la diferencia entre dato de campo y dato satelital.

## ADDED Requirements

### Requirement: Registro de sesión de lecturas
El sistema MUST aceptar en `POST /api/v1/plots/{id}/field-readings` una sesión con: id, fecha, dispositivo (modelo y rango del sensor si se conoce), frecuencia de muestreo (Hz), masa del carro (kg), altura de caída (mm) y puntos con ubicación (lat/lon) y golpes (pico de desaceleración en m/s² o g y duración del pulso en ms).

#### Scenario: Sesión válida
- **GIVEN** el lote `demo-casilda` y una sesión con 4 puntos de 6 golpes cada uno
- **WHEN** se envía la sesión
- **THEN** la respuesta confirma la sesión con su id, el resumen por punto y la lista de limitaciones

#### Scenario: Lote inexistente
- **WHEN** se envía una sesión para el lote `no-existe`
- **THEN** la respuesta es un error tipado `PLOT_NOT_FOUND` con formato `{code, message, details}`

### Requirement: Registro idempotente por sesión
Reenviar una sesión con el mismo id y el mismo contenido MUST NOT duplicarla y MUST devolver el mismo resultado. Reenviar el mismo id con contenido distinto MUST rechazarse con `SESSION_CONFLICT`. Las sesiones MUST poder listarse con `GET /api/v1/plots/{id}/field-readings`.

#### Scenario: Reenvío por mala conexión
- **WHEN** el celular reenvía la misma sesión dos veces
- **THEN** existe una sola sesión guardada y ambas respuestas son idénticas

#### Scenario: Mismo id, otro contenido
- **WHEN** se envía un id de sesión ya guardado con un golpe distinto
- **THEN** la respuesta es `SESSION_CONFLICT` y la sesión original no cambia

### Requirement: Validación de lecturas
Cada golpe MUST tener pico > 0 y duración > 0. La frecuencia de muestreo MUST ser >= el mínimo de A-FLD-02 y la altura de caída MUST ser la estándar de v0 de A-FLD-02 (150 mm de ejemplo, la menor del accesorio, porque el acelerómetro del celular satura). Cada punto MUST estar en el bounding box de Argentina y en el polígono del lote si existe.

#### Scenario: Muestreo insuficiente
- **GIVEN** A-FLD-02 con frecuencia mínima de ejemplo 100 Hz
- **WHEN** la sesión declara 50 Hz
- **THEN** la sesión se rechaza con `SAMPLING_RATE_TOO_LOW` indicando el mínimo

#### Scenario: Altura distinta de la estándar de v0
- **GIVEN** A-FLD-02 con alturas de ejemplo 150, 300 y 450 mm y estándar de v0 150 mm
- **WHEN** la sesión declara 300 mm
- **THEN** la sesión se rechaza indicando que v0 solo admite 150 mm porque el acelerómetro del celular satura en alturas mayores

#### Scenario: Punto fuera del lote
- **WHEN** un punto cae fuera del polígono del lote
- **THEN** la sesión se rechaza nombrando el punto

### Requirement: Golpes saturados y descartados
Un golpe cuyo pico iguala o supera el rango declarado del sensor MUST marcarse `SATURATED` y excluirse del agregado. El primer golpe de cada punto MUST descartarse como asentamiento si A-FLD-01 así lo define. Un punto con menos golpes válidos que el mínimo A-FLD-01 MUST quedar `INSUFFICIENT_IMPACTS` sin índice.

#### Scenario: Sensor saturado
- **GIVEN** un dispositivo con rango declarado 16 g
- **WHEN** un golpe registra 16 g
- **THEN** el golpe queda `SATURATED`, no entra en la mediana y el punto informa cuántos golpes saturaron

#### Scenario: Pocos golpes válidos
- **GIVEN** A-FLD-01 con mínimo de ejemplo 4 golpes válidos
- **WHEN** un punto tiene 5 golpes, uno descartado por asentamiento y uno saturado
- **THEN** el punto queda `INSUFFICIENT_IMPACTS` y no recibe índice

### Requirement: Agregado por punto
Para cada punto con golpes suficientes, el sistema MUST calcular la mediana del pico y de la duración de los golpes válidos y su coeficiente de variación. Si el coeficiente de variación del pico supera A-FLD-03, el punto MUST marcarse `INCONSISTENT` y quedar excluido de la normalización.

#### Scenario: Punto consistente
- **WHEN** un punto tiene golpes válidos con picos 30, 32, 31, 29 y 33 g
- **THEN** la mediana del pico es 31 g y el punto queda `OK`

#### Scenario: Punto inconsistente
- **GIVEN** A-FLD-03 con coeficiente de variación máximo de ejemplo 0.3
- **WHEN** los picos válidos de un punto tienen coeficiente de variación 0.5
- **THEN** el punto queda `INCONSISTENT` y no recibe índice relativo

### Requirement: Normalización relativa no calibrada
Con al menos A-FLD-04 puntos `OK` en la misma sesión y dispositivo, el índice relativo de cada punto MUST ser 100 × mediana del punto / mediana de las medianas de la sesión, y su categoría MUST ser `LOWER`, `MIDDLE` o `HIGHER` por terciles de posición, con desempate por id de punto. Con menos puntos, MUST NOT calcularse índice.

#### Scenario: Índice relativo
- **GIVEN** 3 puntos `OK` con medianas 20, 30 y 40 g y A-FLD-04 = 3 (ejemplo)
- **WHEN** se normaliza
- **THEN** los índices son 66.7, 100 y 133.3, con categorías `LOWER`, `MIDDLE` y `HIGHER`

#### Scenario: Muy pocos puntos
- **WHEN** la sesión tiene 2 puntos `OK` con A-FLD-04 = 3
- **THEN** no hay índices, el resultado dice `NOT_ENOUGH_POINTS` y muestra solo las medianas por punto

#### Scenario: Sin mezcla de sesiones
- **WHEN** se piden índices de dos sesiones de días o dispositivos distintos
- **THEN** cada sesión se normaliza por separado y los índices no se combinan

### Requirement: Procedencia de mediciones de campo
Cada golpe y mediana por punto MUST ser OBSERVED con Source `dataset=FIELD_HAMMER`, variable, fecha de la sesión, dispositivo, resolución puntual e `is_modeled=false`. El índice relativo y la categoría MUST ser DERIVED y citar el supuesto A-FLD-05 sobre su interpretación.

#### Scenario: Procedencia del índice
- **WHEN** se serializa el índice relativo de un punto
- **THEN** su procedencia es DERIVED, `derived_from` incluye las medianas de la sesión y la lista de supuestos incluye A-FLD-05

### Requirement: Limitaciones explícitas
Toda respuesta con lecturas o índices MUST incluir una lista de limitaciones en lenguaje simple: valores relativos no calibrados; dependen de la humedad del suelo, del rastrojo y de la técnica; el sensor puede saturar; miden la capa superficial y no un piso de arado profundo; no comparables entre días, lotes ni celulares.

#### Scenario: Limitaciones presentes
- **WHEN** se consulta cualquier sesión
- **THEN** la respuesta incluye las cinco limitaciones y la frase "no reemplaza un penetrómetro ni la recorrida del agrónomo"

### Requirement: Dato de campo frente a satélite
La consulta de una sesión MUST incluir, para la fecha de la sesión, la humedad SMAP L4 `sm_rootzone` del lote (o la más cercana anterior dentro de A-FLD-06) con su procedencia, y una comparación textual de escala (punto vs ~9 km), profundidad (superficie vs 0 a 100 cm) y tipo de dato. MUST NOT calcular correlaciones ni ajustar SMAP con el campo.

#### Scenario: Tarjeta campo vs satélite
- **GIVEN** una sesión del 2026-11-14 y SMAP L4 disponible para el 2026-11-12
- **WHEN** se consulta la sesión
- **THEN** la respuesta muestra los índices por punto y la humedad SMAP con su fecha real, resolución ~9 km y la explicación de por qué no son directamente comparables

#### Scenario: Sin SMAP para la fecha
- **WHEN** no hay SMAP L4 en caché para la fecha ni dentro de la tolerancia
- **THEN** la respuesta muestra las lecturas y un Faltante de SMAP, sin inventar el dato satelital

#### Scenario: Humedad del suelo como advertencia
- **WHEN** la humedad SMAP de la fecha está disponible
- **THEN** la respuesta recuerda que con suelo más seco los impactos suben y que comparar sesiones con humedad distinta no es válido

### Requirement: Sin efecto en el puntaje del motor
Las lecturas de campo MUST NOT modificar el puntaje, el ranking ni la factibilidad de ninguna rotación, ni completar el indicador de compactación del Suelo de forma automática. Solo MUST poder aparecer como Evidencia de campo en la vista de la web.

#### Scenario: Ranking intacto
- **GIVEN** una evaluación del lote de demo
- **WHEN** se registra una sesión de lecturas y se vuelve a evaluar con la misma entrada
- **THEN** el `input_hash` y la salida del motor son idénticos

### Requirement: Demo con caja de tierra suelta y compactada
El repo MUST incluir una sesión de ejemplo de demo con dos cajas de tierra (suelta y compactada a mano), dos puntos por caja, tomada con el accesorio v0 de A-FLD-02. Normalizada en una sola sesión, los puntos de la caja compactada MUST tener índice relativo mayor que los de la suelta, con categorías ordenadas.

#### Scenario: Suelta contra compactada
- **GIVEN** la sesión de demo con 4 puntos OK, 2 en la caja suelta y 2 en la compactada, A-FLD-04 = 3 (ejemplo)
- **WHEN** se normaliza la sesión
- **THEN** los dos índices de la caja compactada son mayores que los dos de la suelta, ninguno de la compactada queda `LOWER` y ninguno de la suelta queda `HIGHER`

#### Scenario: Cajas con orden invertido
- **GIVEN** una sesión de demo donde la caja compactada no da índices mayores
- **WHEN** corre el test de la demo
- **THEN** el test falla y pide repetir la toma revisando altura, masa y técnica, sin ajustar los números
