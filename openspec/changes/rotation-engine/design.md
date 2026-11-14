# Design: rotation-engine

## Context

Ver proposal.md. Paquete `rastrojo.engine`, función pública `evaluate(inp: EngineInput) -> EngineOutput`. Depende solo de `rastrojo.domain` y de los submódulos puros `water` (water-feasibility), `water_adjust`, `economics`, `soil`, `risk`, `priorities` (solo pesos efectivos de ΔSuelo). La capa `application` arma el EngineInput (desde caché, fixtures y request) y es la única que hace I/O.

## Goals / Non-Goals

**Goals:** una tubería lineal y legible (generar → evaluar → filtrar → puntuar → rankear → empaquetar); determinismo byte a byte; nunca esconder opciones.

**Non-Goals:** búsqueda sobre rotaciones arbitrarias; paralelismo (N candidatas <= 6, el costo es trivial).

## Decisions

### 1. Tubería

```
scen    = apply_year_filter(inp.scenarios, inp.year_class_filter)   # re-pondera, P1
cands   = dedupe_cyclic(inp.catalog ∪ {inp.current})           # orden por id
for r in cands (orden por id):
    wat   = water.assess(r, inp.water_inputs, inp.soil, scen, inp.assumptions)
    adj   = water_adjustments(wat.state_by_scenario)            # NOT_SOWN / FORCE_DRY
    eco   = economics(r, inp.econ, scen, adj, H, i)             # o MissingEconomicParameter
    w_eff = effective_soil_weights(inp.assumptions, prio)       # w = A-SOIL-01 sin prioridades, P1
    soil  = soil_index(r, inp.soil, inp.assumptions, inp.ndvi_summary, w_eff, scen)  # o MissingAssumptionError
    risk  = expected_shortfall(eco.margins, q, i, H)
    score = eco.npv + α·soil.delta − λ·risk                     # exactamente, sin términos extra
    reasons = constraints(r, profile, eco.peak_capital, adj, machinery)
delta_vs_current(results); rank(results); package(EngineOutput)
```

Se evalúa todo antes de filtrar para poder mostrar el puntaje de las descartadas ("te la saqué por capital, pero hubiera salido segunda").

Equivalencia cíclica: forma canónica = la rotación mínima lexicográfica entre sus L rotaciones cíclicas, comparando tuplas (cultivo de invierno o "", cultivo de verano o "") por campaña.

### 2. Estado hídrico: penalizar, excluir solo el caso degenerado

water-feasibility da FEASIBLE/RISKY/NOT_FEASIBLE por (cultivo, posición, escenario). Decisión:

- **Actualizado 14/11 (revisión del equipo):** NOT_FEASIBLE → FORCE_DRY y RISKY solo castiga el rinde si es por perfil no recargado; el estrés moderado ya no baja el rinde porque la clase del año ya lo refleja (antes castigaba dos veces y dejaba márgenes irreales). La humedad inicial de cada campaña sale de GWETROOT de NASA POWER (A-WAT-18).
- **Versión original: NOT_FEASIBLE → NOT_SOWN** (no se siembra ese año: ni costo ni ingreso). La decisión de sembrar doble cultivo o servicio se toma mirando el perfil hídrico al momento de siembra, que es lo que mide el balance con SMAP; un productor razonable no siembra. El castigo aparece como menor E[Margen] y mayor Riesgo, sin inventar un rinde de fracaso.
- **RISKY → FORCE_DRY** (rinde de clase DRY). Usa un parámetro que ya existe y tiene fuente; no agrega coeficientes.
- **Exclusión solo si NOT_FEASIBLE en todos los escenarios con estado conocido** (WATER_NEVER_FEASIBLE) y la factibilidad agregada no es UNKNOWN: la rotación tal como se definió nunca ocurre en el registro histórico.
- **UNKNOWN → sin ajuste, elegible, con Faltante.** Decisión: UNKNOWN no es "no apto". Con datos insuficientes el motor no inventa un castigo: los escenarios sin dato no se ajustan, el puntaje se calcula igual, la factibilidad se informa UNKNOWN ("desconocido") con un Faltante que dice qué dato falta, y la presentación (api, web, chat) la ordena junto a RISKY cuando el usuario pide "primero las que no son riesgosas en agua". Alternativas descartadas: no elegible ante UNKNOWN (esconde opciones por falta de datos, contradice "nunca esconder"); FORCE_DRY en los escenarios sin dato (castigo sin evidencia).

Alternativas descartadas:
- **Excluir ante cualquier NOT_FEASIBLE:** con 40 años de registro casi todo doble cultivo tendría algún año malo y desaparecería la opción que justamente queremos discutir con "agua invisible".
- **Rinde cero con costos incurridos:** supone que se siembra a ciegas; exagera el riesgo y contradice el uso de humedad inicial SMAP.
- **Penalización ad hoc en el puntaje:** número inventado sin unidad clara.
- **Umbral de fracción infactible por actor:** útil pero agrega un supuesto más; queda como P2 si AFA lo pide.

Simplificación documentada: si el cultivo de invierno de una campaña doble es NOT_SOWN, el de verano conserva su propio estado y parámetros (no se reemplaza por soja de primera).

### 2b. Factibilidad informada

La factibilidad del resultado es el estado agregado de water-feasibility (peor campaña, con la regla GRACE-FO, orden NOT_FEASIBLE > UNKNOWN > RISKY > FEASIBLE), salvo un ajuste del motor: NOT_FEASIBLE si aplica WATER_NEVER_FEASIBLE. Un escenario excluido ya no fuerza RISKY: water-feasibility renormaliza y, si quedan menos de A-CLI-03 escenarios, la campaña pasa a UNKNOWN. Así hay una sola definición de umbrales (A-WAT-04 a A-WAT-07) y el motor no inventa otra. Alternativa descartada: una factibilidad propia del motor ("RISKY si hay algún ajuste"), que contradecía el estado de water-feasibility.

### 3. Riesgo (fórmula exacta)

Para cada posición p, márgenes M_p,s con pesos w_s (suman 1). Orden ascendente por (M_p,s, año).

```
cola: acumular w_s hasta q; el escenario de borde entra con peso q − Σ_previos
ES_p   = (1/q) · Σ_{s ∈ cola} w'_s · M_p,s
E_p    = Σ_s w_s · M_p,s
Riesgo = AF(i, H) · (1/L) · Σ_p max(0, E_p − ES_p)
AF     = Σ_{t=1..H} (1+i)^−t
```

Es CVaR al nivel q sobre la distribución histórica enumerada del margen anual de cada posición, expresado como faltante respecto de la media y llevado a horizonte con el mismo factor que el VAN (consistente con el promedio de fases de economics). q = A-ACT-05 (ejemplo 1/3, el peor tercil).

Alternativa descartada: **ES sobre la clase DRY de lluvia.** La clase se define por lluvia en ventanas de invierno y verano por separado; una rotación con trigo y maíz tiene dos clasificaciones por año, y además pierde años malos por exceso hídrico o helada. La cola de la propia distribución de márgenes captura cualquier causa y es coherente (subaditiva). La salida igual informa el rango de margen por clase anual (mín, esperado, máx) como evidencia de incertidumbre para explanations.

Alternativa descartada: **varianza o desvío estándar.** Penaliza los años buenos y no tiene la lectura "cuánto perdés en los años malos" que pide BANK.

### 4. Puntaje y ranking

`score = VAN + α·ΔSuelo − λ·Riesgo` (USD/ha), sin términos extra. Alternativa descartada: términos de prioridad de agua e ingreso suplementario con κ (A-ACT-08 y A-ACT-09, retirados por exigir coeficientes inventados; esas preferencias pasan a ordenar la presentación). Clave de orden para elegibles: `(-round(score, 2), round(risk, 2), -round(delta_soil, 2), id)`. No elegibles después: primero las que tienen puntaje con la misma clave, luego las sin puntaje por id. Rango 1..N. `sorted` de Python es estable y la clave es total, por lo que no depende del orden de entrada.

### 4b. Salidas para explicar

- `score_delta_vs_current = score(r) − score(actual)` sin redondear, DERIVED; ausente si alguna de las dos no tiene puntaje. Es el número que explanations usa para comparar contra la actual.
- Rango de margen por clase anual: para cada clase k, con m_s = (1/L)·Σ_p M_p,s, se informan mín, máx y media ponderada dentro de la clase. Sirve para explicar la incertidumbre entre años secos y húmedos, no entra al puntaje.
- Calendarios: suelo desnudo de soil-impact y vulnerabilidad de water-feasibility, copiados al resultado sin recalcular.
- Años con pérdida y margen del peor año: economics los calcula sobre m_s (margen anual promedio sobre posiciones, ya con ajustes hídricos); el motor los copia. Responden "margen en un año malo" y "en cuántos de los N años reales habrías perdido plata" sin fórmulas nuevas ni umbrales: el corte es margen < 0.
- Lluvia sobre suelo desnudo: soil-impact la calcula con la lluvia diaria POWER de cada escenario y el calendario de días sin cultivo vivo ni rastrojo; el motor la copia. No entra a ΔSuelo para no duplicar el componente de cobertura.

### 4c. Filtro por clase de año (P1)

`year_class_filter ∈ {ALL, DRY, NORMAL, WET}` sobre la clase anual (NORMAL se suma para que actor-profiles calcule la robustez por clase). Con DRY, NORMAL o WET se conservan los escenarios de esa clase y se re-ponderan w'_s = w_s / Σ w de los seleccionados; todo lo demás (E, Riesgo, frecuencias de water-feasibility) se calcula sobre ese conjunto. El mínimo de escenarios A-CLI-03 se controla sobre el conjunto completo, para que el filtro no deje todo RISKY por `INSUFFICIENT_SCENARIOS`. La salida declara el filtro y los años usados con advertencia YEAR_CLASS_FILTER_APPLIED. Alternativa descartada: filtrar en la aplicación antes del motor (el filtro quedaría fuera de la salida auditable).

### 4d. Ventanas de maquinaria y prioridades (P1)

- Si el perfil trae ventanas de maquinaria, un cultivo cuyo mes de siembra o cosecha (A-AGR-01) no está en la ventana de esa operación produce MACHINERY_WINDOW_CONFLICT. Sin ventanas, no hay restricción.
- La re-ponderación de w_k la define actor-profiles (A-ACT-07); el motor pasa los pesos efectivos a soil-impact y los informa en la salida. No hay `priority_terms_usd_ha`.

### 5. Determinismo

- Iteración siempre sobre listas ordenadas por id o año; nunca sobre `set` o `dict` sin ordenar.
- `math.fsum` en todas las sumas; sin numpy en el camino crítico (evita diferencias por BLAS).
- Sin `hash()` builtin; el hash de entrada es SHA-256 del JSON canónico de domain-models.
- `ENGINE_VERSION` como constante semver; se incrementa cuando cambia cualquier snapshot (regla en quality).

### 6. Errores

- Entrada inválida: falla la validación Pydantic antes del motor (application devuelve error tipado JSON).
- Errores por rotación (faltantes): se convierten en no elegible + Faltantes, nunca abortan la corrida.
- Error global `NoCandidatesError` solo si catálogo y actual vienen vacíos (imposible con el catálogo fijo, defensivo).

## Supuestos

- A-ACT-05 (nivel q de la cola del Riesgo) se define en actor-profiles.
- A-ACT-07 (multiplicador de prioridades sobre w_k) se define en actor-profiles; A-ACT-08 y A-ACT-09 quedan retirados.
- No se introducen otros supuestos: los ajustes hídricos reutilizan parámetros existentes y la factibilidad usa los umbrales de water-feasibility.

## Risks / Trade-offs

- [NOT_SOWN es optimista en sequías que empiezan después de la siembra] → explanations lo dice; water-feasibility puede distinguir infactibilidad en siembra vs ciclo en una versión posterior.
- [Riesgo escalado por AF parece "un mal año todos los años"] → es la lectura de faltante esperado en la cola por año, documentada en la explicación; λ lo calibra.
- [Catálogo chico] → es deliberado para la demo; la actual definida por el usuario amplía el espacio.

## Open Questions

- Resuelta: las ventanas de maquinaria entran como restricción explícita en P1 (MACHINERY_WINDOW_CONFLICT).
