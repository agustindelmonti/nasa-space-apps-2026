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
Un property test MUST verificar que, con α = 0 y λ = 0, multiplicar por k > 0 todos los valores monetarios de la entrada (precios, costos, flete, arrendamiento, capital máximo y los κ de prioridades A-ACT-08 y A-ACT-09) no cambia el orden de las candidatas, comparando puntajes sin redondear.

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
Un property test MUST verificar, para prioridades generadas en [0, 1], que las propiedades de aversión al riesgo y de peso del suelo siguen valiendo (con ΔSuelo efectivo), que ΔSuelo sigue en [-100, +100] y que con todas las prioridades en 0 la salida es idéntica byte a byte a la de una entrada sin prioridades.

#### Scenario: Prioridades aleatorias
- **GIVEN** prioridades generadas por hypothesis
- **WHEN** λ sube manteniendo el resto fijo
- **THEN** score(A) − score(B) no aumenta para A con mayor Riesgo que B

#### Scenario: Prioridades en cero
- **WHEN** se evalúa con todas las prioridades en 0 y sin prioridades
- **THEN** las salidas canónicas son idénticas
