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
El motor MUST marcar como no elegible, con motivos codificados, toda candidata que: tenga doble cultivo de renta y el actor no lo permita (DOUBLE_CROP_NOT_ALLOWED), tenga servicio y no se permita (COVER_NOT_ALLOWED), supere el capital máximo si existe (WORKING_CAPITAL_EXCEEDED) o tenga siembra o cosecha fuera de las ventanas de maquinaria declaradas (MACHINERY_WINDOW_CONFLICT). Todos los motivos MUST registrarse.

#### Scenario: Actor sin doble cultivo
- **GIVEN** un perfil que no permite doble cultivo
- **WHEN** se evalúa R_WHEAT_SOY2_MAIZE
- **THEN** queda `eligible=false` con motivo DOUBLE_CROP_NOT_ALLOWED y igual se informan su puntaje y desglose

#### Scenario: Capital sin tope
- **GIVEN** un perfil sin capital máximo
- **WHEN** se evalúa cualquier candidata
- **THEN** ninguna recibe WORKING_CAPITAL_EXCEEDED

#### Scenario: Siembra fuera de la ventana de maquinaria
- **GIVEN** ventanas de siembra disponibles solo en octubre y noviembre y soja de segunda con siembra en diciembre según A-AGR-01 (ejemplo)
- **WHEN** se evalúa R_WHEAT_SOY2_MAIZE
- **THEN** queda no elegible con MACHINERY_WINDOW_CONFLICT nombrando SOY_2ND y SOWING

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
Para cada (cultivo, posición, escenario) el motor MUST calcular el estado con water-feasibility como submódulo, desde los insumos de `EngineInput`, y traducirlo así: NOT_FEASIBLE → el cultivo no se siembra ese año (NOT_SOWN); RISKY → usa el rinde de la clase DRY (FORCE_DRY); FEASIBLE → sin ajuste. Si un cultivo es NOT_FEASIBLE en todos los escenarios, la rotación MUST quedar no elegible con motivo WATER_NEVER_FEASIBLE.

#### Scenario: Soja de segunda infactible en años secos
- **GIVEN** soja de segunda NOT_FEASIBLE en los escenarios DRY y FEASIBLE en el resto
- **WHEN** se evalúa R_WHEAT_SOY2_MAIZE
- **THEN** en los años DRY la campaña aporta solo el margen del trigo, la rotación sigue elegible y su factibilidad es RISKY

#### Scenario: Servicio nunca factible
- **GIVEN** centeno NOT_FEASIBLE en todos los escenarios
- **WHEN** se evalúa R_SOY_COVER
- **THEN** queda no elegible con WATER_NEVER_FEASIBLE y factibilidad NOT_FEASIBLE

#### Scenario: Estado hídrico ausente
- **WHEN** water-feasibility no entrega estado para un cultivo en un escenario (por ejemplo, año excluido por `MISSING_WEATHER`)
- **THEN** no se aplica ajuste en ese escenario, la factibilidad de la rotación es al menos RISKY y se emite un Faltante de evaluación hídrica

### Requirement: Factibilidad de la rotación
La factibilidad informada MUST ser el estado agregado de water-feasibility para la rotación, salvo que MUST ser NOT_FEASIBLE si aplica WATER_NEVER_FEASIBLE y al menos RISKY si falta el estado de algún (cultivo, escenario). La salida MUST informar, por cultivo, la fracción ponderada de escenarios con cada ajuste.

#### Scenario: Rotación sin ajustes
- **GIVEN** todos los cultivos FEASIBLE en todos los escenarios y sin déficit regional de GRACE-FO
- **WHEN** se evalúa la rotación
- **THEN** la factibilidad es FEASIBLE y las fracciones de ajuste son 0

#### Scenario: Una sola definición de umbrales
- **GIVEN** water-feasibility devuelve RISKY para la rotación por `SEVERE_STRESS_FREQUENT`
- **WHEN** el motor arma el resultado
- **THEN** la factibilidad informada es RISKY con los motivos de water-feasibility, sin recalcular umbrales

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
El puntaje de cada candidata con datos completos MUST ser score = VAN + α·ΔSuelo − λ·Riesgo + T_prio, con VAN de economics, ΔSuelo de soil-impact, T_prio de actor-profiles (0 sin prioridades) y α, λ, i, H del perfil. El desglose MUST informar los términos en USD/ha y su suma MUST igualar el puntaje redondeado a 2 decimales.

#### Scenario: Desglose del puntaje
- **GIVEN** VAN 1000 USD/ha, ΔSuelo 20, Riesgo 150 USD/ha, α 2 USD/ha por punto y λ 0.5
- **WHEN** se calcula el puntaje
- **THEN** el puntaje es 1000 + 40 − 75 = 965 USD/ha y el desglose muestra 1000, 40, −75 y términos de prioridad 0

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
La salida MUST ser un EngineOutput con `engine_version`, `input_hash`, perfil efectivo, filtro por clase de año efectivo, resultados rankeados y advertencias. Cada resultado MUST incluir E[Margen] por posición, VAN, ΔSuelo, Riesgo, factibilidad, ajustes hídricos, motivos de exclusión, `score_delta_vs_current`, rango de margen por clase, calendarios de suelo desnudo y de vulnerabilidad, y Faltantes.

#### Scenario: Mismo input, mismos bytes
- **WHEN** se evalúa dos veces la misma entrada y se serializa canónicamente
- **THEN** los bytes son idénticos e incluyen el mismo `input_hash` y `engine_version`

### Requirement: Diferencia contra la rotación actual
Para cada candidata con puntaje, el motor MUST calcular `score_delta_vs_current` = puntaje de la candidata − puntaje de la actual, en USD/ha, DERIVED. Si la actual no tiene puntaje (datos faltantes), el campo MUST quedar ausente en todas y MUST emitirse un Faltante que lo explique.

#### Scenario: Diferencia calculada por el motor
- **GIVEN** la actual con puntaje 900 USD/ha y R_MAIZE_SOY con 965 USD/ha (ejemplo)
- **WHEN** se evalúa
- **THEN** R_MAIZE_SOY tiene `score_delta_vs_current` = 65 y la actual tiene 0

#### Scenario: Actual sin puntaje
- **WHEN** la actual queda con MISSING_PARAMETERS
- **THEN** ninguna candidata informa `score_delta_vs_current` y hay un Faltante que lo explica

### Requirement: Rango de margen por clase de año
Para cada candidata con economía completa, el motor MUST informar por clase anual (DRY, NORMAL, WET) el mínimo, la media ponderada y el máximo del margen anual promedio sobre posiciones, en USD/ha, DERIVED. Una clase sin escenarios MUST informarse vacía. Este rango MUST NOT entrar al puntaje.

#### Scenario: Rango con tres clases
- **GIVEN** márgenes anuales de ejemplo DRY 100 y 150, NORMAL 300, WET 500 y 600 USD/ha con pesos iguales
- **WHEN** se arma el rango
- **THEN** DRY es 100/125/150, NORMAL 300/300/300 y WET 500/550/600

#### Scenario: Puntaje intacto
- **WHEN** se agrega o quita el rango de la salida en un test
- **THEN** el puntaje y el ranking no cambian

### Requirement: Calendarios en el resultado
Cada resultado MUST incluir el calendario mensual de suelo desnudo que produce soil-impact y el calendario mensual de vulnerabilidad que produce water-feasibility, copiados sin recalcular y con procedencia DERIVED.

#### Scenario: Calendarios presentes
- **WHEN** se evalúa la entrada del lote demo
- **THEN** cada resultado trae 12 meses de suelo desnudo y el calendario de vulnerabilidad por cultivo

### Requirement: Filtro por clase de año
Si `EngineInput` trae `year_class_filter` DRY o WET, el motor MUST usar solo los escenarios de esa clase anual, re-ponderados w'_s = w_s / Σ w seleccionados, para economía, Riesgo y frecuencias hídricas, controlar A-CLI-03 sobre el conjunto completo y declarar en la salida el filtro, los años usados y la advertencia YEAR_CLASS_FILTER_APPLIED.

#### Scenario: Solo años secos
- **GIVEN** 30 escenarios con 10 DRY anuales y filtro DRY
- **WHEN** se evalúa
- **THEN** solo entran los 10 años DRY, cada uno con peso 0.1, y la salida declara el filtro y los años

#### Scenario: Sin filtro
- **WHEN** el filtro es ALL o está ausente
- **THEN** se usan todos los escenarios con sus pesos originales y ambas entradas tienen el mismo `input_hash` (ausente se canonicaliza como ALL)

#### Scenario: Filtro sin escenarios
- **WHEN** el filtro es WET y no hay escenarios WET
- **THEN** la evaluación falla con el error tipado `EMPTY_YEAR_CLASS` sin resultados parciales
