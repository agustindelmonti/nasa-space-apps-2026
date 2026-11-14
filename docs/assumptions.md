# Registro consolidado de supuestos

Tabla única de todos los supuestos `A-<AREA>-<NN>` citados en los changes de `openspec/changes/`. Áreas permitidas (validadas en `domain-models`): AGR, CLI, WAT, SOIL, ECO, ACT, FLD, DEMO. Los valores son ejemplos o rangos de trabajo, nunca verdades: todos quedan `PENDING_AFA` hasta que AFA los revise. La fuente de verdad ejecutable es `assumptions.yaml`; este documento la resume para la revisión con agrónomos.

Prioridad de validación con AFA: **alta** = cambia el ranking o la factibilidad del lote demo; **media** = cambia números mostrados o advertencias; **baja** = parámetro técnico o de presentación.

| Id | Descripción | Valor ejemplo / rango | Unidad | Fuente | Change que lo define | Prioridad AFA |
|---|---|---|---|---|---|---|
| A-AGR-01 | Calendario de cultivos: fecha representativa de siembra y de cosecha por cultivo del catálogo | soja de segunda: siembra mediados de diciembre (ejemplo) | fecha (día del año) | pendiente AFA | domain-models | alta |
| A-CLI-01 | Límites de las ventanas de invierno y verano de la campaña | invierno 1/5 a 31/10; verano 1/11 a 31/3 | fecha | pendiente AFA | climate-scenarios | alta |
| A-CLI-02 | Máximo de días faltantes de lluvia por ventana para incluir un año | 0 | días | criterio del equipo, pendiente AFA | climate-scenarios | baja |
| A-CLI-03 | Mínimo de años válidos para clasificar una ventana (y para que water-feasibility pueda dar FEASIBLE) | 15 | años | convención de climatologías cortas, pendiente AFA | climate-scenarios | media |
| A-CLI-04 | Diferencia relativa POWER vs IMERG que dispara advertencia | 25 | % | criterio del equipo | climate-scenarios | baja |
| A-CLI-05 | Umbral de T2M_MIN para helada | 0 | °C a 2 m | criterio del equipo, pendiente AFA | water-feasibility | alta |
| A-CLI-06 | Ventanas sensibles a helada por cultivo | trigo: espigazón a floración; soja y maíz: emergencia | fechas por cultivo | pendiente AFA | water-feasibility | alta |
| A-CLI-07 | Frecuencias para severidad LOW, MEDIUM, HIGH de helada y de cada evento del calendario de vulnerabilidad | 0.1 y 0.3 | fracción de años | criterio del equipo | water-feasibility | media |
| A-CLI-08 | Umbral de T2M_MAX para estrés térmico en floración | 35 | °C a 2 m | pendiente AFA | water-feasibility | media |
| A-CLI-09 | Ventanas de floración por cultivo de renta | maíz temprano: enero (ejemplo) | fechas por cultivo | pendiente AFA | water-feasibility | media |
| A-CLI-10 | Percentil de lluvia diaria IMERG que define lluvia extrema | p95 de los días con lluvia | percentil | criterio del equipo, pendiente AFA | water-feasibility | baja |
| A-WAT-01 | Kc por cultivo y etapa (ini, mid, end), duración de etapas y Kc de barbecho | soja Kc mid 1.15 (FAO-56) | adim. y días | FAO-56 Tablas 11 y 12, pendiente AFA | water-feasibility | alta |
| A-WAT-02 | Método de lluvia efectiva | fracción fija 0.8 | fracción | criterio del equipo, pendiente AFA | water-feasibility | alta |
| A-WAT-03 | Fracción de agotamiento p por cultivo | 0.5 | fracción | FAO-56 Tabla 22, pendiente AFA | water-feasibility | media |
| A-WAT-04 | Índice de estrés para MODERATE (también umbral mensual de déficit del calendario) | 0.15 | adim. | criterio del equipo, pendiente AFA | water-feasibility | alta |
| A-WAT-05 | Índice de estrés para SEVERE | 0.40 | adim. | criterio del equipo, pendiente AFA | water-feasibility | alta |
| A-WAT-06 | Frecuencia ponderada máxima de años SEVERE (y de perfil no recargado) para FEASIBLE | 0.20 | fracción de años | criterio del equipo, pendiente AFA | water-feasibility | alta |
| A-WAT-07 | Frecuencia ponderada de años SEVERE por encima de la cual es NOT_FEASIBLE | 0.50 | fracción de años | criterio del equipo, pendiente AFA | water-feasibility | alta |
| A-WAT-08 | Fracción mínima de agua útil a la siembra del cultivo de verano siguiente | 0.5 | fracción | pendiente AFA | water-feasibility | alta |
| A-WAT-09 | Días entre terminación del cultivo de servicio y siembra siguiente | 30 | días | pendiente AFA | water-feasibility | alta |
| A-WAT-10 | Meses recientes y umbral de anomalía TWS que indica déficit regional | últimos 3 meses bajo percentil 20 | meses y percentil | criterio del equipo | water-feasibility | media |
| A-WAT-11 | Rango de profundidad de napa considerada atenuante | 1.5 a 3 | m | pendiente AFA | water-feasibility | media |
| A-WAT-12 | Fracción de agua útil inicial cuando falta SMAP | 0.5 | fracción | criterio del equipo | water-feasibility | baja |
| A-WAT-13 | θ de capacidad de campo y marchitez por clase textural | tabla por textura | m³/m³ | FAO-56 Tabla 19, pendiente AFA | water-feasibility | media |
| A-WAT-14 | Agua útil del perfil por clase textural y valor genérico | tabla por textura | mm | pendiente AFA (cartas de suelo INTA) | water-feasibility | alta |
| A-WAT-15 | Cada campaña se evalúa desde la misma humedad inicial actual, sin encadenar años (simplificación MVP) | n/a | n/a | criterio del equipo, pendiente AFA | water-feasibility | media |
| A-SOIL-01 | Pesos w_k de los 5 componentes de ΔSuelo (cobertura, carbono, N, malezas, raíces) | 0.25 / 0.25 / 0.15 / 0.20 / 0.15 | adim. | pendiente AFA | soil-impact | alta |
| A-SOIL-02 | Persistencia de cobertura del rastrojo post cosecha por cultivo | pendiente | días | pendiente AFA; literatura de rastrojos en siembra directa | soil-impact | alta |
| A-SOIL-03 | Referencia y escala de fracción cubierta | pendiente | fracción | pendiente AFA | soil-impact | media |
| A-SOIL-04 | Aporte de C de rastrojo y biomasa por cultivo (gramíneas > leguminosas) | pendiente | kg C/ha | pendiente AFA; índices de cosecha publicados (INTA) | soil-impact | alta |
| A-SOIL-05 | Aporte de C de mantenimiento de MO y escala | pendiente | kg C/ha/año | pendiente AFA | soil-impact | media |
| A-SOIL-06 | Balance neto de N por cultivo (fijación, extracción, inmovilización) | pendiente | kg N/ha | pendiente AFA | soil-impact | alta |
| A-SOIL-07 | Escala de normalización del balance de N | pendiente | kg N/ha/año | pendiente AFA | soil-impact | media |
| A-SOIL-08 | D_max de especies y peso β diversidad vs invierno | pendiente | adim. | pendiente AFA | soil-impact | media |
| A-SOIL-09 | Coeficiente de efecto radicular por cultivo | pendiente | [0, 1] | pendiente AFA | soil-impact | media |
| A-SOIL-10 | Umbral de NDVI para considerar suelo cubierto (también suelo desnudo observado) | pendiente | NDVI | pendiente AFA; literatura MODIS | soil-impact | media |
| A-SOIL-11 | Tolerancia entre cobertura modelada y observada | pendiente | fracción | pendiente AFA | soil-impact | baja |
| A-ECO-01 | Calendario mensual de egresos por cultivo (fracción de costos directos por mes relativo a la siembra) | pendiente | fracción | pendiente AFA | economics | media |
| A-ECO-02 | Desfase entre cosecha y cobro | pendiente | meses | pendiente AFA | economics | media |
| A-ECO-03 | Mes de inicio del año de campaña y mes de pago del arrendamiento | julio (ejemplo) | mes | pendiente AFA; práctica de contratos | economics | media |
| A-ECO-04 | Conversión de quintales de soja a USD con el precio neto de soja del mismo set | 1 qq = 100 kg | USD/qq | convención; pendiente AFA el precio de referencia | economics | baja |
| A-ACT-01 | Perfil OWNER: H, i, α, λ, restricciones | H 10, i 0.06, α 5, λ 0.3, capital sin tope | años, fracción, USD/ha por punto, adim. | pendiente AFA | actor-profiles | alta |
| A-ACT-02 | Perfil TENANT | H 1, i 0.12, α 0, λ 0.5, capital 400 USD/ha | ídem | pendiente AFA | actor-profiles | alta |
| A-ACT-03 | Perfil COOP | H 5, i 0.08, α 3, λ 0.5, capital sin tope | ídem | pendiente AFA | actor-profiles | alta |
| A-ACT-04 | Perfil BANK | H 3, i 0.10, α 0.5, λ 1.5, capital 600 USD/ha | ídem | pendiente AFA | actor-profiles | alta |
| A-ACT-05 | Nivel q de la cola del expected shortfall de márgenes (Riesgo) | 1/3 | fracción de peso | convención de terciles, pendiente AFA | actor-profiles | alta |
| A-ACT-06 | Límites de sliders | H 1..20, α 0..20, λ 0..3, i 0..0.30 | varias | pendiente AFA | actor-profiles | baja |
| A-ACT-07 | Multiplicador m de las prioridades sobre los pesos w_k de ΔSuelo | 1 | adim. | criterio del equipo, pendiente AFA | actor-profiles | media |
| A-ACT-08 | κ_w del término de prioridad de agua | 100 | USD/ha por unidad de fracción | criterio del equipo, pendiente AFA | actor-profiles | media |
| A-ACT-09 | κ_i del término de ingreso suplementario | 50 | USD/ha por unidad de fracción | criterio del equipo, pendiente AFA | actor-profiles | media |
| A-FLD-01 | Golpes mínimos válidos por punto y descarte del primero como asentamiento | 4 válidos, descartar el primero | golpes | criterio del equipo | field-measurement | baja |
| A-FLD-02 | Frecuencia de muestreo mínima y altura de caída estándar | 100 Hz; 30 cm | Hz, cm | criterio del equipo | field-measurement | baja |
| A-FLD-03 | Coeficiente de variación máximo del pico en un punto | 0.3 | adim. | criterio del equipo | field-measurement | baja |
| A-FLD-04 | Puntos OK mínimos para normalizar una sesión | 3 | puntos | criterio del equipo | field-measurement | baja |
| A-FLD-05 | Interpretación del índice relativo como dureza superficial relativa, proxy no calibrado de compactación | n/a | n/a | pendiente AFA | field-measurement | media |
| A-FLD-06 | Tolerancia de días hacia atrás para tomar SMAP L4 en la tarjeta campo vs satélite | 3 | días | criterio del equipo | field-measurement | baja |
| A-DEMO-01 | Ubicación y superficie del lote `demo-casilda` | lat -33.05, lon -61.15; 100 ha | grados, ha | placeholder del equipo, pendiente AFA | demo-mode | media |
| A-DEMO-02 | Precios de ejemplo por cultivo de renta, con base FOB o disponible | soja 300 USD/t FOB | USD/t | pizarra con fecha, pendiente AFA | demo-mode | alta |
| A-DEMO-03 | Retenciones de ejemplo por cultivo | soja 26 % | fracción | normativa a la fecha de referencia | demo-mode | media |
| A-DEMO-04 | Costos directos de ejemplo por cultivo, incluidos los de servicio | soja 250 USD/ha | USD/ha | márgenes brutos publicados, pendiente AFA | demo-mode | alta |
| A-DEMO-05 | Cosecha (modo y valor), comercialización y flete de ejemplo | cosecha 8 % del ingreso; flete 20 USD/t | fracción, USD/t | márgenes brutos publicados, pendiente AFA | demo-mode | media |
| A-DEMO-06 | Rindes de ejemplo por cultivo y clase de año (DRY, NORMAL, WET) | soja NORMAL 3.5 t/ha | t/ha | estimaciones MAGyP o BCR, pendiente AFA | demo-mode | alta |

Total: 62 supuestos (AGR 1, CLI 10, WAT 15, SOIL 11, ECO 4, ACT 9, FLD 6, DEMO 6).

## Cambios de ids en la reconciliación

- El lote demo usaba `A-FLD-01`, que chocaba con field-measurement (golpes mínimos). Pasa a `A-DEMO-01`.
- Los parámetros económicos de ejemplo usaban `A-ECO-NN`, que se pisaban con `A-ECO-01..04` de economics. Pasan a `A-DEMO-02` a `A-DEMO-06`.
- explanations citaba `A-AGR-04`, que nadie definía, como base de un riesgo de helada; pasa a `A-CLI-05` (umbral de helada).
- Las "ventanas A-AGR" de soil-impact y el "supuesto de calendario del catálogo" de water-feasibility y domain-models eran el mismo concepto sin id: se unifican en `A-AGR-01`.
