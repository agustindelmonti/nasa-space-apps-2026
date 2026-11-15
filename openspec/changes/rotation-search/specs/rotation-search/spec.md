# Spec Delta

## Purpose

Busca de forma exhaustiva y determinista la mejor rotación posible dentro de reglas agronómicas explícitas, usando el mismo motor que rankea el catálogo, y deja el resultado precalculado y auditable.

## ADDED Requirements

### Requirement: Campañas válidas
El generador MUST producir todas las campañas que cumplen las reglas del dominio y las reglas de poda A-AGR-02 (doble cultivo de verano solo después de trigo) y A-AGR-03 (servicio solo antes de un cultivo de verano de primera; sin campañas de solo invierno).

#### Scenario: Doble cultivo solo después de trigo
- **GIVEN** el catálogo de cultivos
- **WHEN** se generan las campañas válidas
- **THEN** soja de segunda y maíz tardío aparecen solo junto con trigo, nunca con un servicio ni solos

#### Scenario: Servicio antes de un cultivo de primera
- **GIVEN** el catálogo de cultivos
- **WHEN** se generan las campañas válidas
- **THEN** cada campaña con vicia, centeno o avena tiene soja de primera o maíz temprano en verano

### Requirement: Rotaciones canónicas sin repetidas
El generador MUST producir las rotaciones de 1 a A-AGR-04 campañas sin repetir ciclos equivalentes (mismo ciclo empezado en otra campaña) ni secuencias periódicas (una campaña repetida).

#### Scenario: Ciclo equivalente
- **GIVEN** las secuencias [A, B, C] y [B, C, A]
- **WHEN** se generan rotaciones
- **THEN** aparece una sola, con un id estable derivado de su clave canónica

#### Scenario: Secuencia periódica
- **GIVEN** la secuencia [A, A]
- **WHEN** se generan rotaciones
- **THEN** no aparece, porque es la rotación [A]

### Requirement: Reglas de ciclo y candidatas siempre incluidas
La búsqueda MUST descartar las rotaciones generadas que no incluyan una gramínea en el ciclo o que repitan la misma especie de verano más de dos campañas seguidas (A-AGR-05), MUST informar cuántas descartó por cada regla, y MUST evaluar siempre el catálogo y la rotación actual aunque no cumplan esas reglas.

#### Scenario: Soja continua
- **GIVEN** la rotación generada [soja de primera]
- **WHEN** se aplican las reglas de ciclo
- **THEN** se descarta por no tener gramínea, salvo que sea la actual o del catálogo

### Requirement: Búsqueda exhaustiva con el motor
La búsqueda MUST evaluar todas las candidatas en una sola llamada al motor y MUST devolver el ranking de elegibles, el frente de Pareto en (margen esperado, ΔSuelo, riesgo) y la diferencia de puntaje entre la mejor encontrada y la mejor del catálogo. El resultado MUST ser idéntico para la misma entrada.

#### Scenario: La mejor encontrada no puede ser peor que la del catálogo
- **GIVEN** un actor y un filtro de año
- **WHEN** se corre la búsqueda
- **THEN** el puntaje de la mejor encontrada es mayor o igual que el de la mejor del catálogo

#### Scenario: Frente de Pareto
- **GIVEN** el ranking de elegibles
- **WHEN** se calcula el frente
- **THEN** ninguna rotación del frente es dominada por otra elegible en margen, ΔSuelo y riesgo a la vez

### Requirement: Precálculo y API sin evaluación por pedido
El sistema MUST guardar la búsqueda de cada perfil predefinido y filtro de año con `input_hash`, `engine_version` y versión del generador, y la API MUST servir ese resultado sin evaluar en el pedido, respondiendo `SEARCH_NOT_PRECOMPUTED` si falta.

#### Scenario: Pedido a la API
- **GIVEN** el precálculo del propietario con todos los años
- **WHEN** se pide `GET /api/v1/rotations/search?actor=OWNER`
- **THEN** la respuesta trae el ranking, el frente de Pareto y los conteos, con el mismo `input_hash` que el fixture
