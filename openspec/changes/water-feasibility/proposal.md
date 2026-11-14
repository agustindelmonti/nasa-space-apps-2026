# Proposal: water-feasibility

**Prioridad:** P0 balance, estado por escenario, estado UNKNOWN para datos insuficientes y calendario de vulnerabilidad de helada y déficit hídrico (demo sábado); P1 regla de lluvia conservadora POWER vs IMERG, contexto GRACE-FO, napa, riesgo de helada, estrés térmico en floración y lluvia extrema en el calendario; P2 vista detallada del balance diario.

## Why

El eje AFA es gestión hídrica: la pregunta real del productor es si le da el agua para el doble cultivo o para un cultivo de servicio sin castigar la soja o el maíz siguiente. Es también la restricción "agua disponible" de la función objetivo. Hace falta un cálculo simple, explicable y determinista que use los datos NASA (ET0 POWER, SMAP L4, lluvia, GRACE-FO) y diga FEASIBLE, RISKY o NOT_FEASIBLE con su porqué, o UNKNOWN ("desconocido") cuando faltan datos, nunca "no apto" por falta de datos.

## What Changes

- Se define un balance hídrico diario tipo balde por campaña: ETc = Kc·ET0 (Kc FAO-56 como supuesto), lluvia efectiva, agua útil del Suelo, estrés cuando el agotamiento supera la fracción fácilmente disponible, drenaje del excedente.
- Se define la humedad inicial desde SMAP L4 (zona de raíces) convertida a mm de agua útil, con respaldo explícito si falta.
- Se evalúa cada campaña en cada escenario histórico (años de `climate-scenarios`), siempre desde la misma humedad inicial actual sin encadenar años (A-WAT-15), y se agrega a un estado con umbrales supuestos A-WAT-NN.
- Se agrega el estado UNKNOWN, distinto de NOT_FEASIBLE: por escenario cuando falta el clima del año y por campaña cuando quedan menos escenarios válidos que A-CLI-03. El motor no descarta por UNKNOWN: sigue elegible, sin ajuste y con Faltante.
- Regla de lluvia conservadora (P1, A-WAT-16): cuando POWER e IMERG están completas para la campaña de un escenario, el balance usa la de menor lluvia acumulada; la clasificación de años sigue solo con POWER.
- Agua útil desde SoilGrids (resuelta en api) se acepta con el motivo `SOIL_AWC_FROM_SOILGRIDS` y un Faltante, igual que el respaldo A-WAT-14.
- Se entrega al motor un estado por (cultivo, posición, escenario) que rotation-engine traduce en ajustes NOT_SOWN o FORCE_DRY.
- Foco en doble cultivo y cultivo de servicio: agua en el perfil a la siembra del cultivo de verano siguiente ("secado del perfil") y consumo del servicio frente a barbecho.
- GRACE-FO como contexto regional que puede subir FEASIBLE a RISKY, nunca decide solo. Napa opcional como atenuante informado.
- Riesgo de helada (T2M_MIN bajo umbral en ventanas sensibles) como Riesgo separado del estado hídrico, cubierto aquí por compartir insumos y escenarios.
- Calendario mensual de vulnerabilidad por cultivo: helada y déficit hídrico (P0), estrés térmico en floración con T2M_MAX y lluvia extrema con IMERG sobre su percentil p95 de ejemplo (P1), con umbrales A-CLI-08 a A-CLI-10.
- Rango hídrico por clase de año (déficit y agua a la siembra: mínimo, media y máximo) para explicar la incertidumbre entre años secos y húmedos.
- Salida con motivos codificados, evidencia, supuestos usados y faltantes. Puro y testeable sin red.

## Capabilities

### New Capabilities
- `water-feasibility`: balance hídrico simplificado por cultivo y campaña sobre escenarios históricos, estado de factibilidad hídrica con porqué, chequeo de secado del perfil, contexto GRACE-FO, napa y riesgo de helada.

### Modified Capabilities
- Ninguna en specs archivadas. Usa los agregados acordados en `domain-models`: series diarias por escenario (lluvia, ET0, T2M_MIN, T2M_MAX, IMERG opcional), humedad inicial SMAP, anomalía TWS y supuestos resueltos dentro de `EngineInput`.

## Impact

- Módulo puro `rastrojo.engine.water` (sin I/O) dentro del motor, invocado por `rotation-engine` para cada candidata; no se precalcula afuera. Su efecto en el puntaje llega por los ajustes NOT_SOWN y FORCE_DRY sobre los márgenes; el Riesgo del motor es el expected shortfall de márgenes de rotation-engine, no un término hídrico aparte.
- Consumidores: `rotation-engine` (estado y ajustes), `explanations` (motivos, evidencia, calendario), `web-demo` (panel "agua invisible" y timeline de vulnerabilidad).
- Supuestos nuevos en `assumptions.yaml`: A-WAT-01 a A-WAT-16 y A-CLI-05 a A-CLI-10 (A-WAT-17 lo define nasa-ingestion).

## Fuera de alcance

- Modelos de cultivo completos (rinde por estrés, fenología dinámica por grados día): el rinde por clase de año viene de parámetros económicos.
- Ascenso capilar cuantitativo desde la napa, anegamiento y excesos hídricos.
- Riego.
- Balance multicapa o distribución vertical de raíces.
