# Design: actor-profiles

## Context

Ver proposal.md. Los valores de los perfiles viven en `assumptions.yaml` (editable por AFA). `fieldshift.engine.profiles` arma PerfilActor validados (domain-models) y `fieldshift.engine.sensitivity` recombina resultados del motor. El caso de uso `application.sensitivity` lo expone a la API.

## Goals / Non-Goals

**Goals:** perfiles trazables, sliders seguros, sensibilidad barata (sin recalcular economía ni suelo) y exacta.

**Non-Goals:** encontrar "el α correcto"; perfiles para agrónomo o contratista.

## Decisions

### 1. Valores de ejemplo (todos ASSUMPTION, PENDING_AFA)

| id | perfil | H (años) | i | α (USD/ha por punto) | λ | doble cultivo | servicio | capital máx (USD/ha) |
|---|---|---|---|---|---|---|---|---|
| A-ACT-01 | OWNER | 10 | 0.06 | 5 | 0.3 | sí | sí | sin tope |
| A-ACT-02 | TENANT | 1 | 0.12 | 0 | 0.5 | sí | sí | 400 (ejemplo) |
| A-ACT-03 | COOP | 5 | 0.08 | 3 | 0.5 | sí | sí | sin tope |
| A-ACT-04 | BANK | 3 | 0.10 | 0.5 | 1.5 | sí | sí | 600 (ejemplo) |

Racional cualitativo (brief): el propietario mira largo plazo y valor del campo (H y α altos); el arrendatario, la campaña (H=1, α=0, tasa alta, capital acotado); la cooperativa, socio rentable y suelo regional (intermedio); el banco, repago y menor riesgo climático (λ alto). Los números son ilustrativos hasta que AFA los revise.

| id | descripción | valor de ejemplo | fuente |
|---|---|---|---|
| A-ACT-05 | nivel q de la cola del expected shortfall | 1/3 (peor tercil) | convención de terciles de climate-scenarios; pendiente AFA |
| A-ACT-06 | límites de sliders | H 1..20, α 0..20, λ 0..3, i 0..0.30 | pendiente AFA (H 1..20 e i 0..1 son además límites de domain-models) |

"Sin tope" se representa como ausencia explícita del capital máximo (campo opcional en PerfilActor, cambio aditivo si domain-models lo hizo obligatorio), nunca como un número grande.

### 2. Perfil personalizado

`custom_profile(base: ActorKind, overrides: ProfileOverrides) -> PerfilActor` con `kind=CUSTOM`, `base_kind`. Overrides con `extra="forbid"`; validación de rangos contra A-ACT-06; procedencia USER_INPUT por campo modificado. El perfil efectivo se copia a EngineInput, por lo que entra en el `input_hash`.

### 3. Sensibilidad

El puntaje es `score_r(α, λ) = VAN_r + α·S_r − λ·R_r`, lineal en cada parámetro. Se evalúa el motor una vez con el perfil base y se recombinan `VAN_r, S_r, R_r` para cada punto de la grilla, reutilizando la misma función de ranking del motor (mismos desempates). La elegibilidad no depende de α ni λ.

```
grid_k     = mín + k·(máx − mín)/(n − 1),  k = 0..n−1   (redondeo canónico a 6 decimales)
quiebre    : para cada par elegible (a, b) con pendientes distintas
  α* = (base_a − base_b) / (S_b − S_a)        base = VAN − λ·R
  λ* = (base_a − base_b) / (R_a − R_b)        base = VAN + α·S
  se informa si mín <= x* <= máx, con el par en orden (gana_antes, gana_después)
```

Pendientes iguales: no hay quiebre (paralelas). Los quiebres se calculan sin redondeo; la grilla usa el ranking con redondeo a 2 decimales del motor, por lo que en un punto exactamente igual a un quiebre puede decidir el desempate (documentado).

Alternativas descartadas:
- **Re-ejecutar el motor completo por punto:** correcto pero n veces más caro y con riesgo de divergencias; la recombinación es exacta por linealidad.
- **Grilla logarítmica:** α = 0 y λ = 0 son casos clave (TENANT) y no entran en escala log.
- **Sensibilidad sobre H o i:** no lineal y cambia el VAN y el Riesgo; queda como P2 vía re-ejecución completa.

### 4. Test de rankings distintos

Test en `tests/demo/test_actor_rankings.py` que carga el fixture demo, evalúa los cuatro perfiles y verifica que el conjunto de tuplas de ids elegibles ordenados tiene tamaño >= 2. Si falla, se revisa el fixture o los supuestos y se documenta el cambio en el registro; el test imprime los rankings para la discusión.

### 5. API

El endpoint concreto lo define `api`. Propuesta: `POST /api/v1/sensitivity` con `{input | lite_request, parameter: "alpha"|"lambda", min, max, n}`. Los perfiles salen por `GET /api/v1/actors/profiles` (ya en xcut.md).

## Risks / Trade-offs

- [Los cuatro perfiles rankean igual con datos reales] → el test lo detecta; la sensibilidad muestra cuánto α o λ hace falta para el quiebre, que también es un mensaje válido en el pitch.
- [Valores de α percibidos como arbitrarios] → se muestran como supuestos y se explica la unidad (USD/ha por punto).

## Open Questions (para AFA)

- ¿Qué horizonte y tasa usan socios propietarios vs arrendatarios al decidir?
- ¿Qué tope de capital de trabajo es realista para un arrendatario típico?
- ¿El banco mira λ (cola) o probabilidad de margen negativo? Si es lo segundo, se agrega como métrica sin cambiar el puntaje.
