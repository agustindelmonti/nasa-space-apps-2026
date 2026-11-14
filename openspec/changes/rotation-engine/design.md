# Design: rotation-engine

## Context

Ver proposal.md. Paquete `fieldshift.engine`, función pública `evaluate(inp: EngineInput) -> EngineOutput`. Depende solo de `fieldshift.domain` y de los submódulos puros `economics`, `soil`, `risk`, `water_adjust`. La capa `application` arma el EngineInput (desde caché, fixtures y request) y es la única que hace I/O.

## Goals / Non-Goals

**Goals:** una tubería lineal y legible (generar → evaluar → filtrar → puntuar → rankear → empaquetar); determinismo byte a byte; nunca esconder opciones.

**Non-Goals:** búsqueda sobre rotaciones arbitrarias; paralelismo (N candidatas <= 6, el costo es trivial).

## Decisions

### 1. Tubería

```
cands   = dedupe_cyclic(inp.catalog ∪ {inp.current})           # orden por id
for r in cands (orden por id):
    adj   = water_adjustments(r, inp.water_status)              # NOT_SOWN / FORCE_DRY
    eco   = economics(r, inp.econ, inp.scenarios, adj, H, i)    # o MissingEconomicParameter
    soil  = soil_index(r, inp.soil, inp.assumptions, inp.ndvi)  # o MissingAssumptionError
    risk  = expected_shortfall(eco.margins, q, i, H)
    score = eco.npv + α·soil.delta − λ·risk
    reasons = constraints(r, profile, eco.peak_capital, adj)
rank(results); package(EngineOutput)
```

Se evalúa todo antes de filtrar para poder mostrar el puntaje de las descartadas ("te la saqué por capital, pero hubiera salido segunda").

Equivalencia cíclica: forma canónica = la rotación mínima lexicográfica entre sus L rotaciones cíclicas, comparando tuplas (cultivo de invierno o "", cultivo de verano o "") por campaña.

### 2. Estado hídrico: penalizar, excluir solo el caso degenerado

water-feasibility da FEASIBLE/RISKY/NOT_FEASIBLE por (cultivo, posición, escenario). Decisión:

- **NOT_FEASIBLE → NOT_SOWN** (no se siembra ese año: ni costo ni ingreso). La decisión de sembrar doble cultivo o servicio se toma mirando el perfil hídrico al momento de siembra, que es lo que mide el balance con SMAP; un productor razonable no siembra. El castigo aparece como menor E[Margen] y mayor Riesgo, sin inventar un rinde de fracaso.
- **RISKY → FORCE_DRY** (rinde de clase DRY). Usa un parámetro que ya existe y tiene fuente; no agrega coeficientes.
- **Exclusión solo si NOT_FEASIBLE en todos los escenarios** (WATER_NEVER_FEASIBLE): la rotación tal como se definió nunca ocurre en el registro histórico.

Alternativas descartadas:
- **Excluir ante cualquier NOT_FEASIBLE:** con 40 años de registro casi todo doble cultivo tendría algún año malo y desaparecería la opción que justamente queremos discutir con "agua invisible".
- **Rinde cero con costos incurridos:** supone que se siembra a ciegas; exagera el riesgo y contradice el uso de humedad inicial SMAP.
- **Penalización ad hoc en el puntaje:** número inventado sin unidad clara.
- **Umbral de fracción infactible por actor:** útil pero agrega un supuesto más; queda como P2 si AFA lo pide.

Simplificación documentada: si el cultivo de invierno de una campaña doble es NOT_SOWN, el de verano conserva su propio estado y parámetros (no se reemplaza por soja de primera).

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

Alternativa descartada: **ES sobre la clase DRY de lluvia.** La clase se define por lluvia en ventanas de invierno y verano por separado; una rotación con trigo y maíz tiene dos clasificaciones por año, y además pierde años malos por exceso hídrico o helada. La cola de la propia distribución de márgenes captura cualquier causa y es coherente (subaditiva). La salida igual informa el margen medio de los años DRY como evidencia para explanations.

Alternativa descartada: **varianza o desvío estándar.** Penaliza los años buenos y no tiene la lectura "cuánto perdés en los años malos" que pide BANK.

### 4. Puntaje y ranking

`score = VAN + α·ΔSuelo − λ·Riesgo` (USD/ha). Clave de orden para elegibles: `(-round(score, 2), round(risk, 2), -round(delta_soil, 2), id)`. No elegibles después: primero las que tienen puntaje con la misma clave, luego las sin puntaje por id. Rango 1..N. `sorted` de Python es estable y la clave es total, por lo que no depende del orden de entrada.

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
- No se introducen otros supuestos: los ajustes hídricos reutilizan parámetros existentes.

## Risks / Trade-offs

- [NOT_SOWN es optimista en sequías que empiezan después de la siembra] → explanations lo dice; water-feasibility puede distinguir infactibilidad en siembra vs ciclo en una versión posterior.
- [Riesgo escalado por AF parece "un mal año todos los años"] → es la lectura de faltante esperado en la cola por año, documentada en la explicación; λ lo calibra.
- [Catálogo chico] → es deliberado para la demo; la actual definida por el usuario amplía el espacio.

## Open Questions

- ¿El contratista (ventanas de maquinaria) entra como restricción en P2? No cambia esta spec si se agrega como nuevo motivo de exclusión.
