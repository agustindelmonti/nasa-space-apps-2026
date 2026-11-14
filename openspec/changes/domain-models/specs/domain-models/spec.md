# Spec Delta

## Purpose

Define el vocabulario de dominio compartido por todas las capas (lote, suelo, cultivo, rotación, actor, economía, clima, evaluación) con validación estricta y procedencia obligatoria en cada número, para que el motor sea determinista y auditable.

## ADDED Requirements

### Requirement: Modelos inmutables y estrictos
Todo modelo de dominio MUST ser inmutable (frozen) y MUST rechazar campos no declarados (extra prohibido). Los campos numéricos MUST declarar unidad en el nombre o en metadatos y MUST validar rango físico plausible.

#### Scenario: Campo desconocido rechazado
- **GIVEN** un payload de Lote con un campo `color` no declarado
- **WHEN** se valida contra el modelo de Lote
- **THEN** la validación falla con un error que nombra el campo `color`

#### Scenario: Modelo no mutable
- **GIVEN** una instancia válida de Rotación
- **WHEN** el código intenta reasignar uno de sus campos
- **THEN** la operación falla y la instancia original queda intacta

#### Scenario: Rango físico inválido
- **WHEN** se valida un Suelo con materia orgánica de 150 %
- **THEN** la validación falla indicando el rango permitido 0 a 100

### Requirement: Valor con procedencia
Todo número que cruce capas (dato NASA, parámetro, resultado del motor) MUST representarse como un valor con procedencia que incluye `value`, `unit` y `provenance`. La procedencia MUST tener `kind` en {OBSERVED, DERIVED, ASSUMPTION, USER_INPUT}.

#### Scenario: Valor observado sin fuente
- **WHEN** se crea un valor con kind OBSERVED sin `source`
- **THEN** la validación falla

#### Scenario: Supuesto sin identificador
- **WHEN** se crea un valor con kind ASSUMPTION sin `assumption_id`
- **THEN** la validación falla

#### Scenario: Valor derivado con insumos
- **GIVEN** un valor DERIVED (por ejemplo, déficit hídrico) calculado a partir de ET0 de POWER y un coeficiente de cultivo supuesto
- **WHEN** se serializa
- **THEN** su procedencia lista los identificadores de los insumos (`derived_from`) y el método de cálculo

### Requirement: Fuente de datos descriptiva
Una fuente (`source`) MUST incluir dataset (enum cerrado: `NASA_POWER`, `SMAP_L4`, `GPM_IMERG`, `GRACE_FO`, `MODIS_NDVI`, `HLS_NDVI`, `SOILGRIDS`, `GLDAS`, `SRTM`, `ECOSTRESS`, `FIELD_HAMMER`), variable, período, resolución espacial y temporal e `is_modeled`. Un supuesto MUST incluir `assumption_id` con formato `A-<AREA>-<NN>` (AREA en AGR, CLI, WAT, SOIL, ECO, ACT, FLD, DEMO), descripción, fuente o "pendiente AFA" y estado de validación.

#### Scenario: Dato de SoilGrids marcado como modelado
- **WHEN** el Suelo se completa con textura proveniente de SoilGrids
- **THEN** la fuente tiene `dataset=SOILGRIDS` e `is_modeled=true`, y el valor es OBSERVED (producto publicado por un tercero), no DERIVED

#### Scenario: Dataset nuevo admitido
- **WHEN** se crea una fuente con `dataset=SRTM`, `ECOSTRESS`, `GLDAS` o `FIELD_HAMMER`
- **THEN** la validación pasa

#### Scenario: Área de supuesto desconocida
- **WHEN** se crea un supuesto con id `A-XYZ-01`
- **THEN** la validación falla listando las áreas permitidas, incluida DEMO

### Requirement: Procedencia de productos modelados externos
Un valor publicado por un producto de modelo o reanálisis externo (SMAP L4, POWER basado en MERRA-2, SoilGrids, GLDAS, mascons GRACE-FO) MUST ser OBSERVED con `is_modeled=true` en su Source. DERIVED MUST reservarse para valores que calcula nuestro sistema (agregaciones, ET0 calculada, balance, índices, márgenes) y MUST listar sus insumos.

#### Scenario: Humedad SMAP L4 tal cual se publica
- **WHEN** se carga un valor 3-horario de `sm_rootzone` de SMAP L4
- **THEN** su procedencia es OBSERVED con `is_modeled=true`

#### Scenario: Media diaria calculada por el sistema
- **WHEN** se calcula la media diaria de SMAP L4 desde los valores 3-horarios
- **THEN** su procedencia es DERIVED con `derived_from` apuntando a la serie OBSERVED

#### Scenario: Formato de assumption_id inválido
- **WHEN** se crea un supuesto con id `kc-soja`
- **THEN** la validación falla indicando el formato `A-<AREA>-<NN>`

### Requirement: Lote
El Lote MUST incluir identificador, nombre, ubicación (lat/lon WGS84 dentro de un bounding box de Argentina), superficie en hectáreas (> 0) y opcionalmente un polígono GeoJSON. Si hay polígono, la ubicación MUST estar contenida en él.

#### Scenario: Coordenadas fuera de Argentina
- **WHEN** se crea un Lote con lat 40.7, lon -74.0
- **THEN** la validación falla indicando que la ubicación está fuera del área soportada

#### Scenario: Lote válido de zona núcleo
- **WHEN** se crea un Lote en el sur de Santa Fe con 100 ha
- **THEN** la validación pasa

### Requirement: Suelo
El Suelo MUST incluir clase textural, materia orgánica (%), agua útil del perfil en mm para la profundidad de raíces declarada, profundidad de napa en metros (opcional) e indicador de compactación (opcional). Cada campo MUST llevar su propia procedencia (USER_INPUT, OBSERVED desde SoilGrids con `is_modeled=true`, o ASSUMPTION).

#### Scenario: Suelo parcial
- **GIVEN** el usuario informa solo materia orgánica
- **WHEN** se arma el Suelo
- **THEN** los campos faltantes quedan explícitamente ausentes (no con un valor por defecto silencioso) y se registran como faltantes de información

### Requirement: Catálogo cerrado de cultivos
El sistema MUST exponer un catálogo cerrado de cultivos para el MVP: soja de primera, soja de segunda, maíz temprano, maíz tardío, trigo, y cultivos de servicio vicia, centeno y avena. Cada cultivo MUST declarar estación (invierno o verano), tipo (renta o servicio), familia (leguminosa o gramínea) y fechas representativas de siembra y cosecha como referencia al supuesto único de calendario de cultivos A-AGR-01, que comparten water-feasibility, soil-impact y economics.

#### Scenario: Calendario desde un único supuesto
- **WHEN** se consultan las fechas de siembra y cosecha de soja de segunda
- **THEN** ambas citan A-AGR-01 y no hay otra fuente de calendario en el código

#### Scenario: Cultivo fuera de catálogo
- **WHEN** una rotación referencia el cultivo `girasol`
- **THEN** la validación falla listando los cultivos permitidos

### Requirement: Rotación como secuencia de campañas
Una Rotación MUST ser una secuencia ordenada de campañas (1 a 4 años de ciclo). Cada campaña MUST contener a lo sumo un cultivo de invierno y a lo sumo un cultivo de verano. La soja de segunda y el maíz tardío MUST ir precedidos por un cultivo de invierno en la misma campaña; un cultivo de renta de invierno y un cultivo de servicio MUST NOT coexistir en la misma campaña.

#### Scenario: Soja de segunda sin antecesor
- **WHEN** una campaña contiene soja de segunda sin cultivo de invierno
- **THEN** la validación falla

#### Scenario: Rotación trigo/soja 2da/maíz válida
- **WHEN** se define un ciclo de 2 campañas: [trigo + soja de segunda], [maíz temprano]
- **THEN** la validación pasa y la rotación expone su longitud de ciclo = 2

### Requirement: Perfil de actor
Un Perfil de actor MUST incluir horizonte H en años (entero 1 a 20), peso de suelo α (>= 0), aversión al riesgo λ (>= 0), tasa de descuento i (0 a 1) y restricciones: permitir doble cultivo, permitir cultivo de servicio y capital de trabajo máximo en USD/ha opcional (ausente significa "sin tope", nunca un número grande).

#### Scenario: Horizonte inválido
- **WHEN** se crea un perfil con H = 0
- **THEN** la validación falla

#### Scenario: Sin tope de capital
- **WHEN** se crea un perfil sin capital máximo
- **THEN** la validación pasa y el campo queda ausente, no con un valor por defecto

### Requirement: Prioridades del productor y ventanas de maquinaria
El Perfil de actor MUST admitir, opcionales: pesos de prioridad en [0, 1] para EROSION_COVER, OM_CARBON, NITROGEN, WEED_CONTROL y ROOTS (uno por componente de ΔSuelo; ausente equivale a 0), y ventanas de maquinaria como meses calendario (1 a 12) por operación SOWING y HARVEST. Ambos MUST ser USER_INPUT y entrar en el `input_hash`. El perfil MUST NOT admitir prioridades WATER ni SUPPLEMENTAL_INCOME.

#### Scenario: Peso de prioridad fuera de rango
- **WHEN** se crea un perfil con prioridad NITROGEN = 1.5
- **THEN** la validación falla indicando el rango 0 a 1

#### Scenario: Prioridad de presentación en el perfil
- **WHEN** se crea un perfil con prioridad WATER
- **THEN** la validación falla por campo no declarado

#### Scenario: Mes de maquinaria inválido
- **WHEN** se declara una ventana de siembra con el mes 13
- **THEN** la validación falla

### Requirement: Parámetros económicos con fuente y fecha
Los parámetros económicos (precio por tonelada con su base FOB o disponible/FAS, retención, costos directos, costo de cosecha con modo fracción del ingreso o USD/ha, comercialización, flete en USD/t, rinde por cultivo y clase de año, y arrendamiento opcional en USD/ha o quintales de soja/ha) MUST ser valores con procedencia y fecha de referencia. Ninguno MUST tener valor por defecto en el código de dominio.

#### Scenario: Precio sin fecha
- **WHEN** se carga un precio de soja sin fecha de referencia
- **THEN** la validación falla

#### Scenario: Precio sin base
- **WHEN** se carga un precio de maíz sin declarar base FOB o disponible
- **THEN** la validación falla

#### Scenario: Arrendamiento con dos unidades
- **WHEN** se carga un arrendamiento con USD/ha y quintales de soja a la vez
- **THEN** la validación falla indicando que se admite una sola unidad

### Requirement: Escenario climático
Un Escenario climático MUST representar un año histórico real (año de inicio de campaña) con clase anual, clase de invierno y clase de verano (DRY, NORMAL, WET cada una), lluvia de cada ventana en mm con procedencia, y peso (>= 0). El conjunto de escenarios de una evaluación MUST tener pesos que sumen 1 (tolerancia 1e-9).

#### Scenario: Clases por estación y anual
- **WHEN** se crea un escenario 2008 con clase anual NORMAL, invierno DRY y verano WET
- **THEN** la validación pasa y las tres clases quedan disponibles por separado

#### Scenario: Pesos que no suman 1
- **WHEN** se arma un conjunto de escenarios con pesos 0.5 y 0.4
- **THEN** la validación falla

### Requirement: Resultado de evaluación
El resultado por rotación MUST incluir: id, rango, puntaje y desglose (VAN, α·ΔSuelo, λ·Riesgo), factibilidad hídrica (FEASIBLE, RISKY, NOT_FEASIBLE o UNKNOWN), `is_current`, `eligible`, `exclusion_reasons`, `water_adjustments`, `score_delta_vs_current`, rango de margen por clase, años con pérdida, margen del peor año, lluvia sobre suelo desnudo, calendarios de suelo desnudo y de vulnerabilidad, y Evidencia, Beneficios, Faltantes y Riesgos.

#### Scenario: Desglose consistente
- **GIVEN** un resultado de evaluación
- **WHEN** se suman los términos del desglose
- **THEN** el total coincide con el puntaje informado con la precisión declarada

#### Scenario: Diferencia contra la actual
- **GIVEN** la rotación actual con puntaje 900 USD/ha y otra con 965 USD/ha (ejemplo)
- **WHEN** se arma el resultado
- **THEN** la otra tiene `score_delta_vs_current` = 65 USD/ha DERIVED y la actual tiene 0

#### Scenario: Rango de margen por clase
- **WHEN** se arma el resultado de una rotación con escenarios de las tres clases anuales
- **THEN** para DRY, NORMAL y WET informa mínimo, esperado y máximo del margen anual en USD/ha con procedencia DERIVED

#### Scenario: Factibilidad desconocida admitida
- **WHEN** se arma un resultado con factibilidad UNKNOWN
- **THEN** la validación pasa y UNKNOWN es un valor distinto de NOT_FEASIBLE en el enum

#### Scenario: Calendarios de 12 meses
- **WHEN** se arma el resultado
- **THEN** el calendario de suelo desnudo tiene 12 entradas mensuales y el de vulnerabilidad tiene, por cultivo, 12 entradas por tipo de evento

### Requirement: Evidencia, faltante y riesgo
Una Evidencia MUST citar dataset, variable, período, valor con unidad y una frase de interpretación. Un Faltante MUST indicar qué dato falta, por qué importa y cómo conseguirlo. Un Riesgo MUST indicar tipo (hídrico, helada, estrés térmico, lluvia extrema, económico, malezas, suelo), severidad (LOW, MEDIUM, HIGH) y su base (evidencia o supuesto).

#### Scenario: Evidencia sin período
- **WHEN** se crea una Evidencia de NDVI sin período
- **THEN** la validación falla

### Requirement: Sobres de entrada y salida del motor
La entrada del motor MUST agrupar, ya resueltos y sin referencias a red: lote, suelo, rotación actual, candidatas, perfil, parámetros económicos, escenarios, supuestos resueltos usados (id → valor), insumos hídricos y filtro opcional por clase de año (ALL, DRY, NORMAL o WET). La salida MUST incluir `engine_version`, `input_hash` (SHA-256 del JSON canónico de la entrada) y los resultados ordenados por rango.

#### Scenario: Hash reproducible
- **GIVEN** dos entradas semánticamente idénticas con claves en distinto orden
- **WHEN** se calcula `input_hash`
- **THEN** ambos hashes son iguales

#### Scenario: Entrada distinta, hash distinto
- **GIVEN** dos entradas que difieren solo en λ
- **WHEN** se calcula `input_hash`
- **THEN** los hashes difieren

#### Scenario: Orden de listas irrelevante para el hash
- **GIVEN** dos entradas iguales salvo que las candidatas y los escenarios vienen en distinto orden de lista
- **WHEN** se calcula `input_hash`
- **THEN** ambos hashes son iguales, porque la canonicalización ordena candidatas por id y escenarios por año

### Requirement: Insumos hídricos y de evidencia en la entrada
`EngineInput` MUST incluir, por escenario, series diarias de lluvia, ET0, T2M_MIN y T2M_MAX con Source (opcionalmente lluvia diaria IMERG, P1); humedad inicial SMAP L4; anomalía TWS de GRACE-FO; y resumen NDVI mensual del lote. water-feasibility MUST calcularse dentro del motor desde estos insumos, no afuera.

#### Scenario: Estado hídrico precalculado rechazado
- **WHEN** se arma un EngineInput con un campo de estado hídrico ya calculado
- **THEN** la validación falla por campo no declarado

#### Scenario: Insumo opcional ausente
- **WHEN** se arma un EngineInput sin anomalía TWS ni resumen NDVI
- **THEN** la validación pasa y ambos quedan explícitamente ausentes para que el motor emita Faltantes

#### Scenario: Supuestos resueltos en la entrada
- **WHEN** el motor usa el valor de A-WAT-01
- **THEN** ese valor viene del mapa de supuestos resueltos de la entrada y su id figura en el `input_hash`

### Requirement: Serialización JSON canónica
El sistema MUST proveer una serialización canónica: UTF-8, claves ordenadas, sin espacios, floats redondeados a la precisión declarada por campo (por defecto 6 decimales) y sin NaN ni infinitos. Toda salida del motor MUST serializarse de esta forma.

#### Scenario: NaN rechazado
- **WHEN** un valor numérico de salida es NaN
- **THEN** la serialización falla con un error tipado en lugar de emitir `NaN`

#### Scenario: Ida y vuelta estable
- **GIVEN** una salida del motor serializada canónicamente
- **WHEN** se parsea y se vuelve a serializar
- **THEN** los bytes son idénticos
