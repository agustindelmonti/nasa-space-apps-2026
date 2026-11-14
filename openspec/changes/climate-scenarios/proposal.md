# Proposal: climate-scenarios

**Prioridad:** P0 (el motor necesita escenarios para E[Margen] y Riesgo en la demo del sábado).

## Why

La función objetivo calcula esperanza y riesgo sobre años históricos reales enumerados, no con Monte Carlo ni pronósticos. Para que el ranking sea auditable y reproducible, la forma de convertir el registro de lluvia NASA en escenarios seco/normal/húmedo con pesos tiene que ser explícita, determinista y con sus exclusiones a la vista.

## What Changes

- Se define la clasificación de años históricos por terciles de lluvia acumulada en dos ventanas de campaña: invierno y verano (límites de ventana como supuesto A-CLI-01).
- Se definen criterios de completitud: años con huecos por encima de la tolerancia (A-CLI-02) o campañas en curso se excluyen y quedan registrados con motivo.
- Se fija un mínimo de años válidos para clasificar (A-CLI-03); por debajo, no hay clasificación.
- Se fijan pesos 1/N por año, regla de desempate en límites de tercil y redondeo previo a comparar.
- Se define un cruce opcional de la lluvia POWER con GPM IMERG que solo advierte discrepancias (A-CLI-04), sin cambiar la clasificación.
- La clasificación es pura: misma entrada, mismo resultado byte a byte.

## Capabilities

### New Capabilities
- `climate-scenarios`: construcción determinista de conjuntos de EscenarioClimático (año, clase DRY/NORMAL/WET, lluvia de ventana, peso) a partir de series diarias de lluvia, con exclusiones y criterios trazables.

### Modified Capabilities
- Ninguna. Produce instancias de EscenarioClimático de `domain-models`.

## Impact

- Módulo puro `fieldshift.engine.climate` (sin I/O); la aplicación le pasa series de `nasa-ingestion`.
- Consumidores: `rotation-engine` (E[·] y Riesgo), `water-feasibility` (qué años correr el balance), `explanations` (por qué un año es seco).
- Supuestos nuevos en `assumptions.yaml`: A-CLI-01 a A-CLI-04.

## Fuera de alcance

- Pronóstico estacional, ENSO o tendencias de cambio climático.
- Clasificación por índices compuestos (SPI, SPEI, balance hídrico) o por más de tres clases.
- Ponderar años recientes más que antiguos.
- Ventanas por cultivo individuales: se usan las dos ventanas de campaña.
