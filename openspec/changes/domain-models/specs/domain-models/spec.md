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
Una fuente (`source`) MUST incluir dataset (por ejemplo `NASA_POWER`, `SMAP_L4`, `GPM_IMERG`, `GRACE_FO`, `MODIS_NDVI`, `HLS_NDVI`, `SOILGRIDS`), variable, período (inicio y fin), resolución espacial y temporal, y un indicador de si el dato es modelado (`is_modeled`). Un supuesto MUST incluir `assumption_id` con formato `A-<AREA>-<NN>`, descripción, referencia bibliográfica o "pendiente AFA", y estado de validación.

#### Scenario: Dato de SoilGrids marcado como modelado
- **WHEN** el Suelo se completa con textura proveniente de SoilGrids
- **THEN** la fuente tiene `dataset=SOILGRIDS` e `is_modeled=true`, y el valor es DERIVED, no OBSERVED

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
El Suelo MUST incluir clase textural, materia orgánica (%), agua útil del perfil en mm para la profundidad de raíces declarada, profundidad de napa en metros (opcional) e indicador de compactación (opcional). Cada campo MUST llevar su propia procedencia (USER_INPUT, DERIVED desde SoilGrids, o ASSUMPTION).

#### Scenario: Suelo parcial
- **GIVEN** el usuario informa solo materia orgánica
- **WHEN** se arma el Suelo
- **THEN** los campos faltantes quedan explícitamente ausentes (no con un valor por defecto silencioso) y se registran como faltantes de información

### Requirement: Catálogo cerrado de cultivos
El sistema MUST exponer un catálogo cerrado de cultivos para el MVP: soja de primera, soja de segunda, maíz temprano, maíz tardío, trigo, y cultivos de servicio vicia, centeno y avena. Cada cultivo MUST declarar estación (invierno o verano), tipo (renta o servicio), familia (leguminosa o gramínea) y ventanas de siembra y cosecha como referencias a supuestos.

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
Un Perfil de actor MUST incluir horizonte H en años (entero 1 a 20), peso de suelo α (>= 0), aversión al riesgo λ (>= 0), tasa de descuento i (0 a 1) y restricciones (capital de trabajo máximo por mes en USD/ha, permitir doble cultivo, permitir cultivo de servicio).

#### Scenario: Horizonte inválido
- **WHEN** se crea un perfil con H = 0
- **THEN** la validación falla

### Requirement: Parámetros económicos con fuente y fecha
Los parámetros económicos (precio por tonelada, retención %, costos directos, costos de cosecha y flete, rinde por cultivo y clase de año) MUST ser valores con procedencia y MUST incluir fecha de referencia. Ningún parámetro económico MUST tener valor por defecto en el código de dominio.

#### Scenario: Precio sin fecha
- **WHEN** se carga un precio de soja sin fecha de referencia
- **THEN** la validación falla

### Requirement: Escenario climático
Un Escenario climático MUST representar un año histórico real con año, clase (DRY, NORMAL, WET), lluvia de la ventana relevante en mm con procedencia, y peso (>= 0). El conjunto de escenarios de una evaluación MUST tener pesos que sumen 1 (tolerancia 1e-9).

#### Scenario: Pesos que no suman 1
- **WHEN** se arma un conjunto de escenarios con pesos 0.5 y 0.4
- **THEN** la validación falla

### Requirement: Resultado de evaluación
El resultado por rotación MUST incluir: identificador de rotación, rango, puntaje total y su desglose (VAN del margen esperado, término de suelo α·ΔSuelo, término de riesgo λ·Riesgo), estado de factibilidad hídrica (FEASIBLE, RISKY, NOT_FEASIBLE), y las listas de Evidencia, Beneficios, Faltantes y Riesgos. Un indicador `is_current` MUST marcar la rotación actual del productor.

#### Scenario: Desglose consistente
- **GIVEN** un resultado de evaluación
- **WHEN** se suman los términos del desglose
- **THEN** el total coincide con el puntaje informado con la precisión declarada

### Requirement: Evidencia, faltante y riesgo
Una Evidencia MUST citar dataset, variable, período, valor con unidad y una frase de interpretación. Un Faltante MUST indicar qué dato falta, por qué importa y cómo conseguirlo. Un Riesgo MUST indicar tipo (hídrico, helada, económico, malezas, suelo), severidad (LOW, MEDIUM, HIGH) y su base (evidencia o supuesto).

#### Scenario: Evidencia sin período
- **WHEN** se crea una Evidencia de NDVI sin período
- **THEN** la validación falla

### Requirement: Sobres de entrada y salida del motor
La entrada del motor MUST agrupar lote, suelo, rotación actual, rotaciones candidatas o catálogo, perfil de actor, parámetros económicos y escenarios climáticos ya resueltos (sin referencias a red). La salida MUST incluir `engine_version`, `input_hash` (SHA-256 en hex del JSON canónico de la entrada) y los resultados ordenados por rango.

#### Scenario: Hash reproducible
- **GIVEN** dos entradas semánticamente idénticas con claves en distinto orden
- **WHEN** se calcula `input_hash`
- **THEN** ambos hashes son iguales

#### Scenario: Entrada distinta, hash distinto
- **GIVEN** dos entradas que difieren solo en λ
- **WHEN** se calcula `input_hash`
- **THEN** los hashes difieren

### Requirement: Serialización JSON canónica
El sistema MUST proveer una serialización canónica: UTF-8, claves ordenadas, sin espacios, floats redondeados a la precisión declarada por campo (por defecto 6 decimales) y sin NaN ni infinitos. Toda salida del motor MUST serializarse de esta forma.

#### Scenario: NaN rechazado
- **WHEN** un valor numérico de salida es NaN
- **THEN** la serialización falla con un error tipado en lugar de emitir `NaN`

#### Scenario: Ida y vuelta estable
- **GIVEN** una salida del motor serializada canónicamente
- **WHEN** se parsea y se vuelve a serializar
- **THEN** los bytes son idénticos
