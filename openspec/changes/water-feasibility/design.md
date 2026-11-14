# Design: water-feasibility

## Context

Ver proposal.md. Insumos: series diarias por escenario de `nasa-ingestion` (lluvia PRECTOTCORR, ET0, T2M_MIN), escenarios de `climate-scenarios`, humedad SMAP L4 en la fecha de referencia, anomalía TWS de GRACE-FO, Suelo y Rotación de `domain-models`, y valores de supuestos resueltos por la aplicación desde `assumptions.yaml`. Vive en `fieldshift.engine.water`; `rotation-engine` lo llama para cada rotación candidata y usa el estado como restricción y el déficit como insumo de Riesgo.

## Goals / Non-Goals

**Goals:** un cálculo que un agrónomo de AFA pueda revisar en una planilla; estado con porqué; foco en la ventana crítica del doble cultivo y del cultivo de servicio.

**Non-Goals:** predecir rinde por estrés, simular fenología con grados día, ascenso capilar, excesos hídricos.

## Decisions

1. **Balde diario de una capa con Ks de FAO-56** (cap. 8): ETa = Ks·Kc·ET0, Ks = (AU − D)/((1 − p)·AU) cuando D > p·AU. Paso diario porque POWER y la ET0 son diarias y la lluvia no se suaviza. Alternativas descartadas: paso decádico (pierde lluvias grandes y su drenaje), modelo multicapa o AquaCrop (demasiado para el tiempo y difícil de explicar).
2. **Kc en tres etapas (ini, mid, end) con rampas lineales** y duraciones por cultivo, todo en A-WAT-01 tomado de FAO-56 Tablas 11 y 12 como punto de partida. Barbecho con un Kc constante de evaporación (simplificación declarada; FAO-56 tiene un método de evaporación de suelo desnudo más fino que se descarta por tiempo).
3. **Fechas de siembra y cosecha** se toman de la fecha representativa de cada cultivo en el catálogo (supuesto de calendario del catálogo de cultivos, gestionado fuera de este change). La terminación del servicio es la siembra siguiente menos A-WAT-09.
4. **Cada campaña se evalúa por separado desde la misma agua inicial (SMAP de referencia)** con el clima de cada año histórico; dentro de la campaña el balance es continuo (invierno, barbecho, verano). Responde la pregunta de decisión "con el perfil de hoy, qué pasa en cada tipo de año". Alternativa descartada: encadenar campañas con secuencias históricas consecutivas (multiplica combinaciones y mezcla años de distinto tipo sin criterio claro).
5. **Período de la campaña**: del inicio de la ventana de invierno (A-CLI-01) al fin de la ventana de verano, con el año del escenario. El estado se agrega con los pesos recibidos, renormalizados si hay exclusiones.
6. **Umbrales de estado por frecuencia de años severos** (A-WAT-04 a A-WAT-07): fácil de decir en el pitch ("en 9 de 30 años la soja de segunda sufre estrés severo"). Alternativa descartada: umbral sobre el déficit medio (esconde la cola seca, que es lo que le importa al banco y al arrendatario).
7. **GRACE-FO solo escala FEASIBLE a RISKY.** Resolución ~300 km frente a un lote de 100 ha: sirve para decir "la región viene con reservas bajas", no para decidir. "Meses recientes de referencia" y umbral (por ejemplo percentil de la propia serie o cm de anomalía) en A-WAT-10.
8. **Napa solo como atenuante textual.** Sin datos de napa confiables por lote ni tiempo para un modelo de ascenso capilar; sumar agua inventada sería peor que no sumarla. Se puede revisar con AFA.
9. **Helada aquí y no en otro change**: usa los mismos escenarios y series POWER y produce un Riesgo de tipo helada para `rotation-engine` y `explanations`. No toca el estado hídrico para no mezclar conceptos.
10. **Motivos codificados** (`SEVERE_STRESS_FREQUENT`, `MODERATE_STRESS`, `PROFILE_NOT_RECHARGED_AT_SOWING`, `GRACE_REGIONAL_DEFICIT`, `SHALLOW_WATER_TABLE_MITIGATES`, `INITIAL_MOISTURE_ASSUMED`, `SOIL_AWC_ASSUMED`, `SCENARIOS_EXCLUDED`, `INSUFFICIENT_SCENARIOS`, `MISSING_WEATHER`) con parámetros numéricos; las plantillas de `explanations` los traducen a texto.
11. **Agregado en domain-models**: `EngineInput` necesita `daily_weather_by_year` (lluvia, ET0, T2M_MIN como PValue o series con Source), `initial_soil_moisture` (SMAP) y `tws_anomaly` (GRACE-FO). Cambio aditivo a coordinar con el dueño de `domain-models`.

## Supuestos introducidos

| Id | Descripción | Valor de ejemplo | Fuente |
|---|---|---|---|
| A-WAT-01 | Kc por cultivo y etapa (ini, mid, end), duración de etapas y Kc de barbecho | Tablas FAO-56 (ej. soja Kc mid 1.15) | FAO-56 Tablas 11-12, pendiente AFA |
| A-WAT-02 | Método de lluvia efectiva | fracción fija 0.8 | criterio del equipo, pendiente AFA |
| A-WAT-03 | Fracción de agotamiento p por cultivo | 0.5 | FAO-56 Tabla 22, pendiente AFA |
| A-WAT-04 | Índice de estrés para MODERATE | 0.15 | criterio del equipo, pendiente AFA |
| A-WAT-05 | Índice de estrés para SEVERE | 0.40 | criterio del equipo, pendiente AFA |
| A-WAT-06 | Frecuencia ponderada máxima de años SEVERE para FEASIBLE (y de perfil no recargado) | 0.20 | criterio del equipo, pendiente AFA |
| A-WAT-07 | Frecuencia ponderada de años SEVERE por encima de la cual es NOT_FEASIBLE | 0.50 | criterio del equipo, pendiente AFA |
| A-WAT-08 | Fracción mínima de agua útil a la siembra del cultivo de verano siguiente | 0.5 | pendiente AFA |
| A-WAT-09 | Días entre terminación (secado) del cultivo de servicio y siembra siguiente | 30 días | pendiente AFA |
| A-WAT-10 | Meses recientes y umbral de anomalía TWS que indica déficit regional | últimos 3 meses bajo percentil 20 de la serie | criterio del equipo |
| A-WAT-11 | Rango de profundidad de napa considerada atenuante | 1.5 a 3 m | pendiente AFA |
| A-WAT-12 | Fracción de agua útil inicial cuando falta SMAP | 0.5 | criterio del equipo |
| A-WAT-13 | θ de capacidad de campo y marchitez por clase textural | tabla por textura | FAO-56 Tabla 19, pendiente AFA |
| A-WAT-14 | Agua útil del perfil por clase textural y valor genérico | tabla por textura | pendiente AFA (INTA cartas de suelo) |
| A-CLI-05 | Umbral de T2M_MIN para helada | 0 °C a 2 m | criterio del equipo, pendiente AFA |
| A-CLI-06 | Ventanas sensibles a helada por cultivo | trigo: espigazón-floración; soja y maíz: emergencia | pendiente AFA |
| A-CLI-07 | Frecuencias para severidad LOW, MEDIUM, HIGH del riesgo de helada | 0.1 y 0.3 | criterio del equipo |

## Risks / Trade-offs

- [Kc y umbrales genéricos de FAO-56 no calibrados para la zona núcleo] → todos son supuestos PENDING_AFA visibles; la salida muestra cómo cambia el estado si se editan.
- [Agua útil y θ por textura muy gruesos] → Faltante explícito y pedido de dato al usuario.
- [SMAP de una celda de 9 km como estado inicial del lote] → limitación declarada en la evidencia; el usuario puede corregir con dato propio (USER_INPUT) en el futuro.
- [T2M a 2 m subestima heladas a nivel de cultivo] → aclaración en el Riesgo; umbral editable.
- [Ignorar napa subestima la factibilidad en lotes con napa somera] → atenuante informado y pregunta abierta a AFA.

## Supuestos abiertos para AFA

- Kc y duración de etapas de soja de primera y segunda, maíz temprano y tardío, trigo, vicia, centeno y avena en el sur de Santa Fe.
- Agua útil típica de los Argiudoles de la zona y qué fracción a la siembra consideran mínima para la soja de segunda y para la soja tras un servicio.
- Con cuántos días de anticipación secan el cultivo de servicio.
- Qué frecuencia de años malos aceptaría un socio para considerar el doble cultivo "riesgoso" o "no factible".
- Si la napa en la zona hoy está a profundidades que aportan y cómo la miden.
- Umbral de helada y ventanas críticas que usan.

## Open Questions

- Nombre y forma exacta del agregado en `EngineInput` (decisión 11), a acordar con el dueño de `domain-models`; no cambia este spec.
