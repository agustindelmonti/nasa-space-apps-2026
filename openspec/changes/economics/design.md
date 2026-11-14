# Design: economics

## Context

Ver proposal.md. Módulo puro `rastrojo.engine.economics`. Entrada: Rotación validada, ParámetrosEconómicos (domain-models), escenarios con clase por estación (climate-scenarios), H e i del PerfilActor y los ajustes hídricos por (cultivo, posición, escenario) que rotation-engine deriva del estado de water-feasibility (NOT_SOWN o FORCE_DRY, ver rotation-engine design). Salida: matriz de márgenes, márgenes esperados, VAN y capital de trabajo.

## Goals / Non-Goals

**Goals:** fórmulas cerradas, auditables, sin valores ocultos; independencia del orden de campañas; un único lugar donde se convierte un parámetro en USD/ha.

**Non-Goals:** flujo de caja financiero completo (intereses del capital de trabajo, IVA); optimizar fecha de venta.

## Decisions

### 1. Fórmulas

Para cultivo de renta c en escenario s, con clase k = clase del escenario en la estación de c (o DRY si el ajuste es FORCE_DRY; si el ajuste es NOT_SOWN el cultivo aporta 0 en ingresos y costos):

```
P_net_c   = P_c · (1 − ret_c)        si base = FOB
          = P_c                      si base = SPOT (disponible/FAS)
IN_c,s    = Y_c,k · P_net_c                              [USD/ha]
COS_c,s   = cos_frac_c · IN_c,s      o  cos_usd_ha_c     (modo declarado)
COM_c,s   = com_frac_c · IN_c,s
FL_c,s    = flete_usd_t_c · Y_c,k
MB_c,s    = IN_c,s − CD_c − COS_c,s − COM_c,s − FL_c,s
MB_serv   = − CD_c                                         (cultivo de servicio)
M_p,s     = Σ_{c ∈ C_p} MB_c,s − ARR                      (ARR = 0 y lease_included=false si falta)
ARR       = arr_usd_ha  o  arr_qq · 0.1 t/qq · P_net_SOY  (P_net de SOY_1ST)
E_p       = Σ_s w_s · M_p,s                              (math.fsum, orden por año)
```

Y en t/ha (el dominio guarda kg_ha; se divide por 1000 en un solo punto).

### 2. VAN con promedio de fases

```
AF(i, H)  = Σ_{t=1..H} (1+i)^−t
VAN(r)    = (1/L) · Σ_{φ=0..L−1} Σ_{t=1..H} E_{(t−1+φ) mod L} · (1+i)^−t
          = AF(i, H) · Ē,     Ē = (1/L) · Σ_p E_p
```

La igualdad vale porque, promediando sobre fases, cada año t ve cada posición con peso 1/L. Así el ciclo parcial (H no múltiplo de L) queda tratado sin sesgo y el VAN no depende de qué campaña se escribió primero. Se implementa con la forma cerrada `AF·Ē` y un test compara contra la suma explícita por fases.

Alternativas descartadas:
- **Empezar siempre por la campaña 1 y truncar:** [maíz],[soja] y [soja],[maíz] darían VAN distintos con H impar; es la misma rotación.
- **Inferir la fase desde la rotación actual del lote:** requiere saber qué se sembró la última campaña; no está en la entrada del MVP (posible P2).
- **Prorratear el último ciclo:** equivale al promedio de fases solo si los márgenes son parejos; más difícil de explicar.

### 3. Capital de trabajo

Mes 1 = inicio del año de campaña (A-ECO-03). Calendario por cultivo (A-ECO-01): fracciones de CD por mes relativo al mes de siembra (suman 1). Cosecha, comercialización y flete se imputan en el mes de cosecha. Ingreso esperado `Σ_s w_s IN_c,s` en mes de cosecha + desfase (A-ECO-02). Arrendamiento en el mes de pago (A-ECO-03). Meses fuera de los 12 se envuelven al ciclo siguiente en la misma posición (módulo 12) para cultivos de verano cuya cosecha cae en el año calendario siguiente.

```
need_m = max(0, Σ_{j<=m} egresos_j − Σ_{j<=m} ingresos_j)
peak_p = max_m need_m;   peak(r) = max_p peak_p
```

Se usa el máximo sobre posiciones (la campaña más exigente define si el actor la puede financiar). Alternativa descartada: comparar contra el egreso de un solo mes; un actor con poco capital se financia por acumulado, no por mes suelto.

### 3b. Años con pérdida y peor año

```
m_s        = (1/L) · Σ_p M_p,s                  (margen anual promedio del escenario s)
loss_years = { año(s) : m_s < 0 }               conteo |loss_years| de N escenarios usados
worst      = min_s m_s  con su año              (empate: año menor)
```

El corte en 0 no es un supuesto agronómico: es la definición de "perder plata" en margen bruto. El rotulado "margen bruto" se mantiene (sin costos fijos). Alternativas descartadas: percentil bajo de m_s (agrega un parámetro y es más difícil de decir que "el peor año"); probabilidad de pérdida en % (se lee como pronóstico).

### 4. Errores y faltantes

- `MissingEconomicParameter(missing: tuple[(crop_id, param_name), ...])`: se recolecta recorriendo todos los cultivos de la rotación antes de fallar (orden estable: cultivo por id, parámetro por nombre).
- Valores inválidos (precio negativo, retención >= 1) son errores de validación de entrada en domain-models, antes del motor.
- Regla: **error tipado en economics, faltante en la explicación**. economics nunca devuelve números parciales; rotation-engine captura el error por rotación, la marca no elegible y genera un Faltante por par.

### 5. Precisión

Todo en float, sumas con `math.fsum` en orden de lista estable, redondeo solo en la serialización canónica (2 decimales para USD/ha).

## Supuestos introducidos (todos PENDING_AFA)

| id | descripción | unidad | fuente inicial |
|---|---|---|---|
| A-ECO-01 | calendario mensual de egresos por cultivo (fracción de CD por mes relativo a siembra) | fracción | pendiente AFA |
| A-ECO-02 | desfase entre cosecha y cobro | meses | pendiente AFA |
| A-ECO-03 | mes de inicio del año de campaña (ejemplo: julio) y mes de pago del arrendamiento | mes | pendiente AFA; práctica de contratos de arrendamiento |
| A-ECO-04 | conversión de quintales de soja a USD con precio neto de soja del mismo set | USD/qq | convención 1 qq = 100 kg; pendiente AFA para el precio de referencia |

Los rindes por clase, precios, retenciones y costos del lote demo son parámetros con su propia procedencia en el fixture (USER_INPUT o ASSUMPTION A-DEMO-02 a A-DEMO-06, definidos en demo-mode); economics no introduce valores. El calendario de siembra y cosecha que usa A-ECO-01 es A-AGR-01 (domain-models).

## Risks / Trade-offs

- [Arrendamiento no cambia el ranking] → es un término constante por año para todas las rotaciones; impacta solo en el capital de trabajo y en el margen mostrado. Se documenta en la explicación para TENANT.
- [Margen positivo engañoso sin costos fijos] → la salida lo rotula "margen bruto".
- [Precios con fechas mezcladas] → advertencia en salida (ver spec).

## Open Questions (para AFA)

- Calendario típico de egresos y modalidad de cosecha (porcentaje vs USD/ha) en sur de Santa Fe.
- Arrendamiento típico (qq/ha) y momento de pago para socios de AFA.
