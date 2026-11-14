# Design: climate-scenarios

## Context

Ver proposal.md. Entrada: series diarias de lluvia con faltantes explícitos producidas por `nasa-ingestion` (formato largo con `is_missing`). Salida: EscenarioClimático de `domain-models`. Vive en `fieldshift.engine.climate` porque es pura y la reusa el motor, pero la aplicación la invoca antes de armar `EngineInput` (el motor recibe escenarios ya resueltos).

## Goals / Non-Goals

**Goals:** clasificación simple de explicar en el pitch ("de los últimos N años, el tercio más seco"), reproducible y con exclusiones visibles.

**Non-Goals:** índices estandarizados, estadística de extremos, optimizar la elección de ventanas.

## Decisions

1. **Terciles por rango, no por cuantil interpolado.** Ordenar por (lluvia redondeada a 0.1 mm, año) y cortar por posición floor(N/3). Garantiza clases de tamaño fijo y elimina ambigüedad en empates. Alternativa descartada: `numpy.quantile` con umbrales (depende del método de interpolación y en empates cambia el tamaño de las clases); alternativa descartada: asignar empates a la misma clase (tamaños variables, pesos de clase menos estables).
2. **Redondeo a 0.1 mm antes de comparar** con `round()` de Python sobre la suma `math.fsum` de los días. La resolución práctica de la lluvia diaria es de décimas de mm; el redondeo absorbe ruido de orden de suma.
3. **Resto a NORMAL.** Con N mod 3 != 0 los años sobrantes caen en NORMAL para que DRY y WET sean simétricas.
4. **Pesos 1/N por año** (frecuencia empírica), coherentes con xcut. La probabilidad de clase es la frecuencia (aprox. 1/3). Alternativa descartada: pesos por clase 1/3 repartidos dentro de cada clase (equivale salvo por el resto y complica la explicación).
5. **Dos clasificaciones independientes (invierno y verano).** Un año puede ser DRY en invierno y WET en verano. economics usa la clase de la estación de cada cultivo. Alternativa descartada: usar solo una ventana anual (mezcla el riesgo del trigo con el de la soja); la clase anual se agrega además de las estacionales (decisión 9), no en su lugar.
6. **Fuente por defecto POWER PRECTOTCORR** por cobertura desde 1981 (más años, terciles más estables). IMERG (0.1°, más fino) solo como cruce y advertencia. Alternativa descartada: clasificar con IMERG (menos años, 2000+) o promediar ambos (mezcla de fuentes poco trazable).
7. **Tolerancia de faltantes como supuesto** (A-CLI-02) con valor de ejemplo 0 días: preferimos excluir años antes que completar lluvia inventada. Si deja muy pocos años, el equipo puede subirla con justificación.
8. **API interna**: `classify_years(series: RainSeries, window: WindowDef, cfg: ClassificationConfig) -> ClassificationResult`, todo modelos frozen. Sin acceso a `assumptions.yaml`: la aplicación resuelve los valores de A-CLI-01..04 y los pasa en `cfg` con su procedencia.
9. **Escenario combinado y clase anual**: los años válidos en ambas ventanas forman el conjunto que entra a `EngineInput`; la clase anual usa terciles de la lluvia de campaña sobre ese conjunto. Pesos 1/N del conjunto combinado. economics usa la clase estacional de cada cultivo; el filtro por clase de año y el rango de margen usan la anual. Alternativa descartada: derivar la clase anual de las dos estacionales (no hay regla natural para DRY + WET).

## Supuestos introducidos

| Id | Descripción | Valor de ejemplo | Fuente |
|---|---|---|---|
| A-CLI-01 | Límites de las ventanas de invierno y verano de la campaña | invierno 1/5 a 31/10; verano 1/11 a 31/3 | pendiente AFA |
| A-CLI-02 | Máximo de días faltantes de lluvia por ventana para incluir el año | 0 días | criterio del equipo, pendiente AFA |
| A-CLI-03 | Mínimo de años válidos para clasificar una ventana | 15 años | criterio del equipo (convención de climatologías cortas), pendiente AFA |
| A-CLI-04 | Diferencia relativa POWER vs IMERG que dispara advertencia | 25 % | criterio del equipo |

## Risks / Trade-offs

- [Lluvia POWER sesgada frente a pluviómetros del lote] → cruce con IMERG y limitación visible; los terciles son relativos al propio registro, lo que reduce el efecto del sesgo constante.
- [Tercil por posición separa años con lluvia casi igual] → se publica `tie_breaks` y los límites; se explica que la clase es una etiqueta para agrupar, no un umbral agronómico.
- [Cambio de ventanas por AFA cambia rankings] → es esperado; la salida cita A-CLI-01 y el hash de entrada cambia.

## Supuestos abiertos para AFA

- ¿Las ventanas de invierno y verano del ejemplo reflejan las campañas del sur de Santa Fe? ¿Conviene una ventana de barbecho invernal distinta para el cultivo de servicio?
- ¿Qué cantidad mínima de años consideran representativa?

## Open Questions

- Ninguna que cambie el spec: los valores concretos de A-CLI-01..04 se ajustan en `assumptions.yaml`.
