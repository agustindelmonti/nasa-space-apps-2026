# Spec Delta

## Purpose

Garantiza mediante verificaciones automáticas en cada push que el motor es determinista, puro y coherente con propiedades esperables del ranking, que el lote demo no cambia sin aviso y que el código del núcleo cumple estándares estáticos.

## ADDED Requirements

### Requirement: Determinismo en el mismo proceso
La suite MUST incluir un test que evalúe la entrada del lote demo dos veces en el mismo proceso, para cada perfil predefinido, y compare los bytes del JSON canónico de ambas salidas. Cualquier diferencia MUST hacer fallar el test mostrando la primera ruta JSON distinta.

#### Scenario: Dos corridas iguales
- **WHEN** se corre el test de determinismo sobre el lote demo con OWNER, TENANT, COOP y BANK
- **THEN** las cuatro parejas de salidas son idénticas byte a byte

### Requirement: Determinismo entre procesos
La suite MUST incluir un test que ejecute el motor en dos subprocesos independientes con valores distintos de `PYTHONHASHSEED`, sin red, sobre la misma entrada serializada, y compare los bytes de las salidas canónicas y sus SHA-256.

#### Scenario: Semillas de hash distintas
- **GIVEN** dos subprocesos con `PYTHONHASHSEED=1` y `PYTHONHASHSEED=2`
- **WHEN** cada uno evalúa la entrada demo y escribe la salida canónica a su salida estándar
- **THEN** los SHA-256 de ambas salidas coinciden

### Requirement: Propiedad de aversión al riesgo
Un property test MUST verificar que, para entradas generadas válidas, subir λ manteniendo el resto fijo nunca mejora la posición relativa de la candidata elegible de mayor Riesgo frente a otra elegible de menor Riesgo, comparando puntajes sin redondear.

#### Scenario: Más λ no favorece a la más riesgosa
- **GIVEN** dos elegibles A y B con Riesgo de A mayor que el de B
- **WHEN** λ pasa de λ1 a λ2 > λ1
- **THEN** score(A) − score(B) con λ2 es menor o igual que con λ1

### Requirement: Propiedad de peso del suelo
Un property test MUST verificar que subir α nunca empeora el rango de la candidata elegible con mayor ΔSuelo, excluyendo los casos en que la diferencia de puntaje con otra candidata es menor que la precisión de redondeo (0.01 USD/ha).

#### Scenario: Más α no penaliza a la que más mejora el suelo
- **GIVEN** la candidata elegible C con el mayor ΔSuelo y rango k con α1
- **WHEN** α pasa a α2 > α1
- **THEN** el rango de C con α2 es menor o igual que k

### Requirement: Propiedad de permutación
Un property test MUST verificar que permutar el orden de las candidatas y de los escenarios en la entrada no cambia el ranking ni los bytes de la salida canónica, incluido el `input_hash`, porque la canonicalización de domain-models ordena candidatas por id y escenarios por año.

#### Scenario: Candidatas reordenadas
- **WHEN** se evalúa la misma entrada con las candidatas en una permutación aleatoria generada por hypothesis
- **THEN** la lista de ids rankeados, todos los resultados y el `input_hash` son idénticos

### Requirement: Propiedad de escala monetaria
Un property test MUST verificar que, con α = 0 y λ = 0, multiplicar por k > 0 todos los valores monetarios de la entrada (precios, costos, flete, arrendamiento y capital máximo) no cambia el orden de las candidatas, comparando puntajes sin redondear.

#### Scenario: Precios por k
- **GIVEN** α = 0, λ = 0 y un factor k generado en (0.1, 10)
- **WHEN** se escalan todos los valores monetarios por k
- **THEN** el orden por puntaje sin redondear es el mismo y cada VAN se multiplica por k con tolerancia relativa 1e-9

### Requirement: Snapshots del lote demo
La suite MUST guardar la salida canónica del lote demo para cada perfil predefinido como snapshot versionado. Un cambio de snapshot MUST requerir actualización explícita y MUST acompañarse de un incremento de `engine_version`; un test MUST fallar si el snapshot cambió y la versión no.

#### Scenario: Cambio de fórmula sin bump
- **GIVEN** un cambio en el motor que altera el puntaje de una rotación demo
- **WHEN** se actualiza el snapshot sin cambiar `engine_version`
- **THEN** el test de coherencia snapshot-versión falla

### Requirement: Cobertura mínima
El CI MUST medir cobertura de líneas y ramas del paquete engine y fallar si es menor a 90 %; domain MUST medirse con el mismo umbral.

#### Scenario: Cobertura insuficiente
- **WHEN** un cambio deja la cobertura de engine en 87 %
- **THEN** el job de tests del CI falla con el porcentaje informado

### Requirement: Calidad estática
El CI MUST correr ruff (lint y chequeo de formato) sobre todo el código Python y mypy en modo estricto sobre engine y domain; cualquier error MUST hacer fallar el CI.

#### Scenario: Tipo faltante en engine
- **WHEN** se agrega en engine una función sin anotaciones de tipo
- **THEN** mypy estricto falla en el CI

### Requirement: Pureza verificada por análisis de imports
Un test MUST analizar estáticamente (AST, sin importar módulos) todos los archivos de engine y fallar si importan módulos de red, tiempo, aleatoriedad, sistema o concurrencia, SDKs de LLM, o las capas data, application o adapters. También MUST fallar ante llamadas a `now()`, `today()` o `utcnow()`.

#### Scenario: Import prohibido
- **WHEN** un archivo de engine contiene `import random` o `from fieldshift.data import cache`
- **THEN** el test falla nombrando el archivo, la línea y el módulo

#### Scenario: Engine limpio
- **WHEN** engine solo importa la biblioteca estándar permitida, domain y sus propios módulos
- **THEN** el test pasa

### Requirement: CI sin red ni secretos
El workflow de GitHub Actions MUST correr en cada push y pull request ruff, mypy, pytest con cobertura, determinismo y test de imports, usando solo fixtures del repo, sin secretos y con los tests marcados como de red excluidos.

#### Scenario: Push a una rama
- **WHEN** se hace push de un commit
- **THEN** el workflow corre todos los jobs y su resultado queda visible en el commit sin requerir secretos

### Requirement: Propiedades con prioridades del productor
Un property test MUST verificar, para prioridades de suelo generadas en [0, 1], que las propiedades de aversión al riesgo y de peso del suelo siguen valiendo (con ΔSuelo efectivo), que ΔSuelo sigue en [-100, +100], que el desglose tiene solo VAN, α·ΔSuelo y λ·Riesgo y que con todas las prioridades en 0 la salida es idéntica byte a byte a sin prioridades.

#### Scenario: Prioridades aleatorias
- **GIVEN** prioridades generadas por hypothesis
- **WHEN** λ sube manteniendo el resto fijo
- **THEN** score(A) − score(B) no aumenta para A con mayor Riesgo que B

#### Scenario: Prioridades en cero
- **WHEN** se evalúa con todas las prioridades en 0 y sin prioridades
- **THEN** las salidas canónicas son idénticas

### Requirement: Datos insuficientes dan UNKNOWN y no no factible
Un test MUST verificar que una entrada con menos escenarios con clima completo que A-CLI-03 produce factibilidad UNKNOWN con Faltante, que la rotación sigue elegible con puntaje y que ni el resultado ni las explicaciones contienen NOT_FEASIBLE, "no factible" ni "no apta" para esa rotación.

#### Scenario: Pocos años con clima
- **GIVEN** la entrada demo recortada a 10 años con clima completo y A-CLI-03 = 15 (ejemplo)
- **WHEN** se evalúa y se generan las explicaciones
- **THEN** las rotaciones afectadas son UNKNOWN, elegibles, con Faltante, y el texto dice "desconocida"

### Requirement: Lenguaje prohibido en todas las salidas
Un test MUST aplicar la lista prohibida versionada de explanations (que incluye "% de confianza", "predice" y "garantiza") a los textos generados de las fixtures de demo, a los textos estáticos de `web/src` y al material de `docs/demo/`, y MUST fallar nombrando archivo y expresión. Las leyendas fijas MUST quedar permitidas.

#### Scenario: Porcentaje de confianza en la web
- **WHEN** un componente de la web contiene "% de confianza"
- **THEN** el test falla nombrando el archivo

#### Scenario: Leyenda permitida
- **WHEN** un texto contiene "Son escenarios con años históricos, no una predicción."
- **THEN** el test pasa

### Requirement: Entregables de transparencia
Un test MUST verificar que existen `AI_USE.md` y `PRIOR_WORK.md` en la raíz del repo, no vacíos, y que el README los enlaza. Quality MUST NOT redactarlos: los crea el ingeniero principal.

#### Scenario: Falta PRIOR_WORK.md
- **WHEN** se borra `PRIOR_WORK.md` en una rama
- **THEN** el test falla nombrando el archivo faltante

### Requirement: Fuente de cada número del pitch y la página NASA
Un test MUST extraer, con el parser de formato argentino de explanations, todos los números de `docs/demo/nasa-page.md` y de los guiones del pitch y del video, y MUST verificar que cada uno figura en la tabla `docs/demo/sources.md` (número, dataset o supuesto, archivo cacheado o id) y que cada archivo citado existe en el manifiesto de fixtures. Tiempos de guion y números de orden MUST excluirse por lista cerrada.

#### Scenario: Número sin fuente
- **GIVEN** un guion que dice "9 de 30 años" sin fila en `docs/demo/sources.md`
- **WHEN** corre el test
- **THEN** el test falla nombrando el número y el archivo

#### Scenario: Archivo citado inexistente
- **WHEN** una fila de `docs/demo/sources.md` cita un parquet que no está en el manifiesto
- **THEN** el test falla nombrando la fila

### Requirement: Preferencias de presentación sin efecto en el motor
En P1 un test MUST verificar que evaluar con y sin `display_preferences` produce el mismo `engine_output`, el mismo `input_hash` y los mismos rangos, y que `display_order` es una permutación de los ids donde cada grupo conserva el orden de rango.

#### Scenario: Preferencias combinadas
- **WHEN** se evalúa la entrada demo con WATER_SAFE_FIRST y DOUBLE_CROP_FIRST
- **THEN** `engine_output` es idéntico byte a byte al de la evaluación sin preferencias

### Requirement: Chequeo de años secos documentado
En P1 un test MUST verificar que existe `docs/validation.md` con el reporte del chequeo de años DRY contra rindes MAGyP de climate-scenarios, que cita fuente y fecha de descarga y A-CLI-11, y que el archivo de rindes no es leído por el motor ni por el armado de `EngineInput`.

#### Scenario: Reporte sin fuente
- **WHEN** `docs/validation.md` no cita la fuente MAGyP
- **THEN** el test falla
