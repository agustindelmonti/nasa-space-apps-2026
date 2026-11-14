# Design: actor-profiles

## Context

Ver proposal.md. Los valores de los perfiles viven en `assumptions.yaml` (editable por AFA). `fieldshift.engine.profiles` arma PerfilActor validados (domain-models) y `fieldshift.engine.sensitivity` recombina resultados del motor. El caso de uso `application.sensitivity` lo expone a la API.

## Goals / Non-Goals

**Goals:** perfiles trazables, sliders seguros, sensibilidad barata (sin recalcular economía ni suelo) y exacta, robustez del ranking sin porcentajes.

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
| A-ACT-07 | multiplicador m de las prioridades sobre los pesos w_k de ΔSuelo | 1 (prioridad 1 duplica el peso antes de renormalizar) | criterio del equipo, pendiente AFA |

A-ACT-08 y A-ACT-09 (κ de los términos de agua e ingreso suplementario) quedan REJECTED en `docs/assumptions.md`: no inventar valores; reemplazados por filtro de presentación.

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

`api` publica `POST /api/v1/sensitivity` con `{mode: lite|full, input, parameter: "alpha"|"lambda", min, max, n, year_class_filter?}`. Los perfiles salen por `GET /api/v1/actors/profiles`.

### 6. Prioridades del productor (P1)

Pesos p_k ∈ [0, 1] (USER_INPUT, ausente = 0), uno por componente de ΔSuelo:

```
map 1 a 1: EROSION_COVER→cov, OM_CARBON→carb, NITROGEN→n, WEED_CONTROL→weed, ROOTS→root
w'_k  = w_k·(1 + m·p_k) / Σ_j w_j·(1 + m·p_j)         m = A-ACT-07, w = A-SOIL-01
score = VAN + α·ΔSuelo(w') − λ·Riesgo                 (sin términos agregados)
```

Propiedades: con todas las prioridades en 0, w' = w (salida idéntica a sin prioridades). ΔSuelo sigue en [-100, 100] porque w' suma 1 y los componentes no cambian. El puntaje sigue lineal en α y λ, la sensibilidad sigue exacta y las propiedades de quality se mantienen.

Prioridades de agua e ingreso suplementario: se sacan del perfil y del motor. Pasan a ser preferencias de presentación (`display_preferences` en api: WATER_SAFE_FIRST y DOUBLE_CROP_FIRST) que reordenan la lista mostrada con una partición estable sin cambiar puntajes, rangos ni `input_hash`. Alternativas descartadas: términos monetarios con κ_w y κ_i (A-ACT-08 y A-ACT-09, retirados: exigían inventar USD/ha por fracción sin fuente); prioridades que modifican α o λ (mezclan dos sliders con el mismo efecto); mapear EROSION_COVER a cobertura y raíces a la vez (menos legible que el mapa 1 a 1).

### 6b. Robustez del ranking (P1)

Caso de uso `application.robustness`: corre el motor con el perfil efectivo y `year_class_filter` ∈ {DRY, NORMAL, WET} (3 corridas) y con los 4 perfiles predefinidos sin filtro (4 corridas). Por rotación informa `first_in_year_classes` (lista y conteo sobre las clases con escenarios) y `first_in_profiles` (lista y conteo sobre 4). "Primera" = rango 1 entre elegibles. Solo conteos: sin porcentajes ni etiquetas como "robusta" que requerirían un umbral inventado. Alternativa descartada: probabilidad de quedar primero con remuestreo (aleatorio, no determinista).

### 7. Ventanas de maquinaria (P1)

El productor declara meses disponibles para SOWING y HARVEST. Se copian al PerfilActor efectivo (entran al `input_hash`) y rotation-engine marca MACHINERY_WINDOW_CONFLICT. Sin ventanas no hay restricción. La sensibilidad no cambia la elegibilidad porque las ventanas no dependen de α ni λ.

## Risks / Trade-offs

- [Los cuatro perfiles rankean igual con datos reales] → el test lo detecta; la sensibilidad muestra cuánto α o λ hace falta para el quiebre, que también es un mensaje válido en el pitch.
- [Valores de α percibidos como arbitrarios] → se muestran como supuestos y se explica la unidad (USD/ha por punto).

## Open Questions (para AFA)

- ¿Qué horizonte y tasa usan socios propietarios vs arrendatarios al decidir?
- ¿Qué tope de capital de trabajo es realista para un arrendatario típico?
- ¿El banco mira λ (cola) o probabilidad de margen negativo? Si es lo segundo, se agrega como métrica sin cambiar el puntaje. El Riesgo del motor es el expected shortfall de la cola de peso q de los márgenes (A-ACT-05), no el margen de los años de clase DRY.
- ¿Qué prioridades de suelo usan los socios al elegir rotación y cuánto pesan frente al margen (A-ACT-07)?
- ¿En qué meses tienen típicamente maquinaria propia o contratada disponible?
