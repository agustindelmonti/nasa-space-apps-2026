# Spec Delta

## Purpose

Rankea de forma pura y determinista las rotaciones candidatas de un lote para un perfil de actor, combinando VAN del margen esperado, índice de suelo y riesgo climático histórico, respetando restricciones sin esconder opciones y devolviendo una salida auditable con hash de entrada y versión.

## ADDED Requirements

### Requirement: Generación de candidatas
El motor MUST tomar como candidatas las rotaciones del catálogo cerrado incluidas en la entrada más la rotación actual. Si la actual es equivalente a una del catálogo (mismas campañas salvo rotación cíclica del orden), MUST aparecer una sola vez, con el id del catálogo e `is_current=true`; si no, MUST aparecer con su propio id e `is_current=true`.

#### Scenario: Actual igual a una del catálogo
- **GIVEN** la rotación actual [soja de primera], [maíz temprano]
- **WHEN** se generan candidatas
- **THEN** R_MAIZE_SOY aparece una sola vez con `is_current=true` y no hay una entrada duplicada

#### Scenario: Actual definida por el usuario
- **GIVEN** una rotación actual válida [trigo + soja de segunda] que no está en el catálogo
- **WHEN** se generan candidatas
- **THEN** la salida contiene las 5 del catálogo más la actual con `is_current=true`

### Requirement: Restricciones del actor con motivo registrado
El motor MUST marcar como no elegible, con motivos codificados, toda candidata que: tenga doble cultivo de renta en una campaña y el actor no lo permita (DOUBLE_CROP_NOT_ALLOWED), tenga cultivo de servicio y no se permita (COVER_NOT_ALLOWED), o cuyo pico de capital de trabajo supere el máximo del actor (WORKING_CAPITAL_EXCEEDED). Todos los motivos aplicables MUST registrarse, no solo el primero.

#### Scenario: Actor sin doble cultivo
- **GIVEN** un perfil que no permite doble cultivo
- **WHEN** se evalúa R_WHEAT_SOY2_MAIZE
- **THEN** queda `eligible=false` con motivo DOUBLE_CROP_NOT_ALLOWED y igual se informan su puntaje y desglose

#### Scenario: Dos motivos a la vez
- **GIVEN** un perfil que no permite servicio y con capital máximo menor al pico de R_MAIZE_SOY_COVER
- **WHEN** se evalúa R_MAIZE_SOY_COVER
- **THEN** los motivos son COVER_NOT_ALLOWED y WORKING_CAPITAL_EXCEEDED, en ese orden alfabético

### Requirement: Datos faltantes no esconden la rotación
Si economics o soil-impact fallan para una candidata por parámetros o supuestos faltantes, el motor MUST marcarla no elegible (MISSING_PARAMETERS o MISSING_ASSUMPTIONS), sin puntaje, y MUST emitir un Faltante por cada par faltante. La evaluación del resto MUST continuar.

#### Scenario: Falta precio de trigo
- **GIVEN** parámetros económicos sin precio de trigo
- **WHEN** se evalúa la entrada completa
- **THEN** R_WHEAT_SOY2_MAIZE queda no elegible con MISSING_PARAMETERS y un Faltante que nombra WHEAT y price, y las demás candidatas se rankean normalmente

### Requirement: Efecto del estado hídrico
Para cada (cultivo, posición, escenario) el motor MUST traducir el estado de water-feasibility así: NOT_FEASIBLE → el cultivo no se siembra ese año (NOT_SOWN); RISKY → usa el rinde de la clase DRY (FORCE_DRY); FEASIBLE → sin ajuste. Si un cultivo es NOT_FEASIBLE en todos los escenarios, la rotación MUST quedar no elegible con motivo WATER_NEVER_FEASIBLE.

#### Scenario: Soja de segunda infactible en años secos
- **GIVEN** soja de segunda NOT_FEASIBLE en los escenarios DRY y FEASIBLE en el resto
- **WHEN** se evalúa R_WHEAT_SOY2_MAIZE
- **THEN** en los años DRY la campaña aporta solo el margen del trigo, la rotación sigue elegible y su factibilidad es RISKY

#### Scenario: Servicio nunca factible
- **GIVEN** centeno NOT_FEASIBLE en todos los escenarios
- **WHEN** se evalúa R_SOY_COVER
- **THEN** queda no elegible con WATER_NEVER_FEASIBLE y factibilidad NOT_FEASIBLE

#### Scenario: Estado hídrico ausente
- **WHEN** no hay estado hídrico para un cultivo de la rotación
- **THEN** no se aplica ajuste, la factibilidad de la rotación es RISKY y se emite un Faltante de evaluación hídrica

### Requirement: Factibilidad de la rotación
La factibilidad de cada rotación MUST ser NOT_FEASIBLE si aplica WATER_NEVER_FEASIBLE; RISKY si algún cultivo tiene ajuste en al menos un escenario o falta su estado hídrico; FEASIBLE en otro caso. La salida MUST informar, por cultivo, la fracción ponderada de escenarios con cada ajuste.

#### Scenario: Rotación sin ajustes
- **GIVEN** todos los cultivos FEASIBLE en todos los escenarios
- **WHEN** se evalúa la rotación
- **THEN** la factibilidad es FEASIBLE y las fracciones de ajuste son 0

### Requirement: Riesgo como expected shortfall
Para cada posición p del ciclo, el motor MUST ordenar los márgenes por escenario de menor a mayor (empate por año ascendente), tomar la cola de peso acumulado q (supuesto A-ACT-05, con fracción del escenario de borde) y calcular ES_p como su media ponderada. Riesgo = AF(i,H) · promedio sobre p de max(0, E_p − ES_p), en USD/ha y >= 0.

#### Scenario: Cola de un tercio exacta
- **GIVEN** una rotación de un cultivo, tres escenarios de peso 1/3 con márgenes 100, 200 y 600 USD/ha, q = 1/3, H=1, i=0
- **WHEN** se calcula el Riesgo
- **THEN** E = 300, ES = 100 y Riesgo = 200 USD/ha

#### Scenario: Escenario de borde fraccionado
- **GIVEN** cuatro escenarios de peso 0.25 con márgenes 0, 100, 200, 300 y q = 1/3
- **WHEN** se calcula ES
- **THEN** ES = (0.25·0 + (1/3 − 0.25)·100) / (1/3) = 25 USD/ha

#### Scenario: Sin variabilidad
- **WHEN** todos los escenarios tienen el mismo margen
- **THEN** el Riesgo es 0

### Requirement: Función objetivo
El puntaje de cada candidata con datos completos MUST ser score = VAN + α·ΔSuelo − λ·Riesgo, con VAN de economics, ΔSuelo de soil-impact y α, λ, i, H del perfil de actor. El desglose MUST informar los tres términos en USD/ha y su suma MUST igualar el puntaje redondeado a 2 decimales.

#### Scenario: Desglose del puntaje
- **GIVEN** VAN 1000 USD/ha, ΔSuelo 20, Riesgo 150 USD/ha, α 2 USD/ha por punto y λ 0.5
- **WHEN** se calcula el puntaje
- **THEN** el puntaje es 1000 + 40 − 75 = 965 USD/ha y el desglose muestra 1000, 40 y −75

### Requirement: Ranking estable y determinista
Las candidatas elegibles MUST ordenarse por puntaje redondeado a 2 decimales descendente, luego menor Riesgo, luego mayor ΔSuelo, luego id lexicográfico. Las no elegibles MUST ir después, con el mismo criterio si tienen puntaje y por id las que no. El rango MUST ser 1..N sin huecos.

#### Scenario: Empate en puntaje
- **GIVEN** dos elegibles con puntaje 965.004 y 964.996 y Riesgo 100 y 80
- **WHEN** se rankea
- **THEN** ambos redondean a 965.00 y gana la de Riesgo 80

#### Scenario: Orden de entrada irrelevante
- **WHEN** se evalúan las mismas candidatas en otro orden de lista
- **THEN** el ranking y los bytes de la salida son idénticos

### Requirement: Al menos tres opciones incluida la actual
La salida MUST contener todas las candidatas, con al menos 3 entradas y la actual siempre presente aunque sea no elegible. Si quedan menos de 3 elegibles, la salida MUST incluir una advertencia LOW_ELIGIBLE_COUNT y las no elegibles con sus motivos en lugar de omitirlas.

#### Scenario: Restricciones muy duras
- **GIVEN** un perfil sin doble cultivo, sin servicio y con capital máximo bajo
- **WHEN** se evalúa
- **THEN** la salida trae todas las candidatas, la actual marcada, la advertencia LOW_ELIGIBLE_COUNT y cada descartada con sus motivos

### Requirement: Pureza del motor
El motor MUST ser una función pura de EngineInput: sin acceso a red, archivos, variables de entorno, reloj, generadores aleatorios ni LLM. Toda constante agronómica, económica o de riesgo MUST llegar en la entrada como parámetro o supuesto resuelto.

#### Scenario: Ejecución sin red
- **GIVEN** un entorno sin red y sin variables de entorno del proyecto
- **WHEN** se evalúa la entrada del lote demo
- **THEN** la evaluación termina con la misma salida que con red

### Requirement: Salida auditable
La salida MUST ser un EngineOutput con `engine_version` (semver del motor), `input_hash` (SHA-256 del JSON canónico de la entrada), el perfil efectivo usado, los resultados rankeados y las advertencias. Para cada resultado MUST incluir E[Margen] por posición, VAN, ΔSuelo, Riesgo, factibilidad, ajustes hídricos, motivos de exclusión y Faltantes.

#### Scenario: Mismo input, mismos bytes
- **WHEN** se evalúa dos veces la misma entrada y se serializa canónicamente
- **THEN** los bytes son idénticos e incluyen el mismo `input_hash` y `engine_version`
