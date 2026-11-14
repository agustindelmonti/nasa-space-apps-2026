# Spec Delta

## Purpose

Evalúa si una rotación es hídricamente factible en el lote (con foco en doble cultivo y cultivo de servicio) mediante un balance hídrico simplificado sobre años históricos reales, y devuelve FEASIBLE, RISKY o NOT_FEASIBLE con su porqué, evidencia NASA, supuestos y riesgo de helada.

## ADDED Requirements

### Requirement: Balance hídrico diario tipo balde
El sistema MUST calcular un balance diario de agua útil (mm) por campaña: agua del día = agua previa + lluvia efectiva − ETa, acotada entre 0 y el agua útil del Suelo; el excedente MUST registrarse como drenaje. ETc MUST ser Kc·ET0 con Kc por cultivo y etapa del supuesto A-WAT-01, incluido un Kc de barbecho entre cultivos.

#### Scenario: Excedente drenado
- **GIVEN** agua útil del Suelo de 150 mm (ejemplo), agua previa 140 mm, lluvia efectiva 30 mm y ETa 4 mm
- **WHEN** se calcula el día
- **THEN** el agua del día es 150 mm y el drenaje del día es 16 mm

#### Scenario: Barbecho entre cultivos
- **WHEN** hay días entre la cosecha de un cultivo y la siembra del siguiente
- **THEN** esos días usan el Kc de barbecho de A-WAT-01 y el resultado lo informa como etapa `FALLOW`

### Requirement: Estrés hídrico por agotamiento
Cuando el agotamiento del perfil supere la fracción fácilmente disponible p·agua útil (p por cultivo según A-WAT-03), el sistema MUST reducir ETa = Ks·ETc con Ks lineal de FAO-56 entre p·agua útil y agua útil. El índice de estrés de un cultivo en un escenario MUST ser 1 − ΣETa/ΣETc sobre su ciclo.

#### Scenario: Sin estrés
- **WHEN** el agotamiento se mantiene por debajo de p·agua útil todo el ciclo
- **THEN** ETa = ETc cada día y el índice de estrés es 0

#### Scenario: Perfil vacío
- **WHEN** el agua del día previo es 0 mm y no llueve
- **THEN** Ks es 0, ETa es 0 mm y el día suma déficit igual a ETc

### Requirement: Lluvia efectiva declarada
La lluvia efectiva MUST calcularse desde la precipitación diaria con el método y parámetros del supuesto A-WAT-02 y MUST quedar como DERIVED con la fuente de lluvia (POWER PRECTOTCORR por defecto, la misma fuente que la clasificación de escenarios). La fuente usada MUST citarse en la evidencia.

#### Scenario: Fracción fija de ejemplo
- **GIVEN** A-WAT-02 definido como fracción fija de ejemplo 0.8
- **WHEN** llueven 20 mm en un día
- **THEN** la lluvia efectiva del día es 16 mm DERIVED con `derived_from` la precipitación de POWER y el id A-WAT-02

### Requirement: Humedad inicial desde SMAP L4
El agua inicial de la campaña MUST derivarse de `sm_rootzone` de SMAP L4 en la fecha de referencia: fracción = (θ − θ marchitez)/(θ capacidad de campo − θ marchitez) acotada a [0, 1], multiplicada por el agua útil. θ de capacidad de campo y marchitez MUST venir del Suelo o del supuesto A-WAT-13 por textura.

#### Scenario: Conversión de SMAP
- **GIVEN** θ = 0.30, capacidad de campo 0.35 y marchitez 0.15 (valores de ejemplo) y agua útil 150 mm
- **WHEN** se calcula el agua inicial
- **THEN** el agua inicial es 112.5 mm DERIVED citando SMAP_L4 `sm_rootzone`, la fecha y A-WAT-13

#### Scenario: Sin SMAP disponible
- **WHEN** no hay valor SMAP para la fecha de referencia
- **THEN** el agua inicial usa la fracción del supuesto A-WAT-12, se agrega el motivo `INITIAL_MOISTURE_ASSUMED` y un Faltante que explica cómo conseguir el dato

### Requirement: Agua útil del Suelo con respaldo explícito
El sistema MUST usar el agua útil (mm) informada en el Suelo. Si falta, MUST usar el valor por clase textural del supuesto A-WAT-14 y, si también falta la textura, el valor genérico de A-WAT-14; en ambos casos MUST agregar el motivo `SOIL_AWC_ASSUMED` y un Faltante. MUST NOT inventar el dato sin marcarlo.

#### Scenario: Suelo sin agua útil
- **GIVEN** un Suelo con textura franco limosa y sin agua útil
- **WHEN** se evalúa la factibilidad
- **THEN** el balance usa el valor de A-WAT-14 para esa textura, el resultado incluye `SOIL_AWC_ASSUMED` y un Faltante "agua útil del perfil"

### Requirement: Evaluación por escenario histórico
Cada campaña de la rotación MUST evaluarse con el clima diario real de cada escenario recibido (año de campaña), partiendo de la misma agua inicial. Un escenario sin lluvia o ET0 completas para el período de la campaña MUST excluirse con motivo y año, sin interpolar, y los pesos MUST renormalizarse a 1/N' entre los restantes.

#### Scenario: Resultado por año
- **WHEN** se evalúa trigo/soja de segunda sobre 30 escenarios
- **THEN** el resultado lista por año: clase del escenario, índice de estrés por cultivo, déficit en mm y agua a la siembra del cultivo de verano

#### Scenario: Año sin ET0 completa
- **GIVEN** 30 escenarios donde 1982 no tiene radiación y por eso no tiene ET0
- **WHEN** se evalúa
- **THEN** 1982 se excluye con motivo `MISSING_WEATHER`, quedan 29 escenarios con peso 1/29 y se agrega el motivo `SCENARIOS_EXCLUDED`

### Requirement: Estado de factibilidad por campaña
Cada escenario MUST etiquetarse por cultivo: SEVERE si el índice de estrés supera A-WAT-05, MODERATE si supera A-WAT-04. La campaña MUST ser FEASIBLE si la frecuencia ponderada de escenarios SEVERE es <= A-WAT-06, NOT_FEASIBLE si es > A-WAT-07 y RISKY en otro caso. La rotación MUST tomar el peor estado de sus campañas.

#### Scenario: Doble cultivo riesgoso
- **GIVEN** A-WAT-06 = 0.2 y A-WAT-07 = 0.5 (ejemplos) y soja de segunda SEVERE en 9 de 30 escenarios
- **WHEN** se agrega la campaña
- **THEN** la frecuencia es 0.3, el estado es RISKY y el motivo `SEVERE_STRESS_FREQUENT` cita 9 de 30 años y los ids A-WAT-05 a A-WAT-07

#### Scenario: Peor campaña manda
- **WHEN** una rotación de dos campañas tiene una FEASIBLE y otra NOT_FEASIBLE
- **THEN** la rotación es NOT_FEASIBLE e indica qué campaña lo determina

#### Scenario: Pocos escenarios válidos
- **WHEN** tras las exclusiones quedan menos escenarios que A-CLI-03
- **THEN** la campaña MUST NOT ser FEASIBLE: queda RISKY con motivo `INSUFFICIENT_SCENARIOS`

### Requirement: Secado del perfil antes del cultivo siguiente
En campañas con doble cultivo o cultivo de servicio, el sistema MUST calcular el agua útil a la siembra del cultivo de verano y su fracción del agua útil total. Si la frecuencia ponderada de escenarios con fracción menor a A-WAT-08 supera A-WAT-06, la campaña MUST ser al menos RISKY con motivo `PROFILE_NOT_RECHARGED_AT_SOWING`.

#### Scenario: Centeno seca el perfil en años secos
- **GIVEN** maíz/soja con centeno de servicio terminado según A-WAT-09 antes de la soja
- **WHEN** en 8 de 30 escenarios el agua a la siembra de la soja queda bajo la fracción A-WAT-08
- **THEN** con A-WAT-06 = 0.2 (ejemplo) la campaña es al menos RISKY con `PROFILE_NOT_RECHARGED_AT_SOWING` listando esos años y su clase

#### Scenario: Terminación del servicio
- **WHEN** se simula un cultivo de servicio
- **THEN** su ciclo termina A-WAT-09 días antes de la siembra del cultivo siguiente y ese intervalo se simula como barbecho

### Requirement: Consumo del cultivo de servicio frente a barbecho
Para cada campaña con cultivo de servicio, el sistema MUST simular también la misma campaña con barbecho en lugar del servicio y MUST informar, por escenario y en promedio ponderado, la diferencia de agua a la siembra del cultivo siguiente en mm como DERIVED.

#### Scenario: Costo hídrico del servicio
- **WHEN** se evalúa soja con vicia de servicio
- **THEN** el resultado informa "agua a la siembra con servicio" y "con barbecho" por año, y la diferencia promedio en mm con procedencia DERIVED

### Requirement: GRACE-FO como contexto regional acotado
Si la anomalía TWS de GRACE-FO de los meses recientes de referencia está por debajo del umbral A-WAT-10, el sistema MUST subir un estado FEASIBLE a RISKY con motivo `GRACE_REGIONAL_DEFICIT`. GRACE-FO MUST NOT producir NOT_FEASIBLE, MUST NOT bajar un estado y su evidencia MUST declarar resolución ~300 km.

#### Scenario: Región seca, lote factible
- **GIVEN** una campaña FEASIBLE por balance y una anomalía TWS bajo A-WAT-10
- **WHEN** se aplica el contexto GRACE-FO
- **THEN** el estado es RISKY con `GRACE_REGIONAL_DEFICIT` y la evidencia aclara que es un dato regional

#### Scenario: GRACE-FO no empeora más
- **WHEN** la campaña ya es RISKY o NOT_FEASIBLE y la anomalía TWS es muy negativa
- **THEN** el estado no cambia y GRACE-FO aparece solo como evidencia

#### Scenario: GRACE-FO no mejora
- **WHEN** la campaña es NOT_FEASIBLE y la anomalía TWS es positiva
- **THEN** el estado sigue NOT_FEASIBLE

#### Scenario: Sin dato GRACE-FO
- **WHEN** no hay anomalía TWS para los meses de referencia
- **THEN** el estado lo decide solo el balance y se agrega un Faltante de contexto regional

### Requirement: Napa opcional como atenuante informado
Si el Suelo informa profundidad de napa dentro del rango A-WAT-11, el sistema MUST agregar el motivo `SHALLOW_WATER_TABLE_MITIGATES` como atenuante sin cambiar el balance ni el estado. Si la napa no está informada, MUST agregar un Faltante que explique por qué importa para el doble cultivo y cómo medirla.

#### Scenario: Napa somera
- **GIVEN** napa a 2 m y A-WAT-11 con rango de ejemplo 1.5 a 3 m
- **WHEN** la campaña de doble cultivo resulta RISKY
- **THEN** sigue RISKY y el resultado incluye `SHALLOW_WATER_TABLE_MITIGATES` con la profundidad informada como USER_INPUT

#### Scenario: Napa desconocida
- **WHEN** el Suelo no informa napa
- **THEN** el resultado incluye un Faltante "profundidad de napa" con cómo conseguirla (freatímetro o registro de la zona)

### Requirement: Riesgo de helada en ventanas sensibles
Por cultivo, el sistema MUST contar los escenarios con al menos un día de T2M_MIN de POWER menor o igual al umbral A-CLI-05 dentro de su ventana sensible A-CLI-06, y MUST emitir un Riesgo de tipo helada con severidad según la frecuencia ponderada y A-CLI-07. Este riesgo MUST NOT modificar el estado hídrico.

#### Scenario: Heladas en floración de trigo
- **GIVEN** A-CLI-05 = 0 °C (ejemplo) y la ventana sensible del trigo de A-CLI-06
- **WHEN** 6 de 30 escenarios tienen T2M_MIN <= 0 °C en esa ventana
- **THEN** se emite un Riesgo helada con frecuencia 0.2, severidad según A-CLI-07, los años afectados y la aclaración de que T2M es temperatura a 2 m de una celda regional

#### Scenario: Helada no cambia factibilidad
- **WHEN** una campaña es FEASIBLE hídricamente y tiene riesgo de helada HIGH
- **THEN** el estado hídrico sigue FEASIBLE y el riesgo de helada se informa por separado

### Requirement: Salida explicable con evidencia y supuestos
El resultado por rotación y campaña MUST incluir: estado, motivos codificados con sus cifras, Evidencias (dataset, variable, período, valor con unidad, interpretación), ids de todos los supuestos usados, Faltantes y Riesgos. Todo número MUST ser un PValue con procedencia.

#### Scenario: Porqué legible
- **WHEN** una campaña resulta RISKY
- **THEN** cada motivo trae los números que lo justifican (por ejemplo frecuencia y años) y al menos una Evidencia de ET0 de POWER y una de humedad de SMAP L4

#### Scenario: Supuestos listados
- **WHEN** se evalúa cualquier rotación
- **THEN** la salida lista al menos A-WAT-01, A-WAT-02, A-WAT-03 y los umbrales de estado usados, con su estado de validación

### Requirement: Evaluación pura y determinista
La evaluación MUST ser pura: recibe series, Suelo, rotación, escenarios y supuestos ya resueltos; no usa red, reloj, aleatoriedad ni archivos. La misma entrada MUST producir la misma salida canónica byte a byte. Las sumas MUST hacerse en orden cronológico estable.

#### Scenario: Repetición idéntica
- **GIVEN** la entrada del lote de demo
- **WHEN** se evalúa dos veces en procesos distintos
- **THEN** las salidas canónicas son idénticas byte a byte

#### Scenario: Sin red
- **WHEN** se evalúa con la red bloqueada
- **THEN** la evaluación termina sin errores y con el mismo resultado
