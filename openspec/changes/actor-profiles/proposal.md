# Proposal: actor-profiles

**Prioridad:** P0 para perfiles predefinidos y test de rankings distintos (es el "mismo lote, rankings distintos" de la demo); P1 para perfiles personalizados, sensibilidad, pesos de prioridades del productor y ventanas de maquinaria.

## Why

El desafío pide contemplar las prioridades del productor, y el brief propone mostrar que el mismo lote se ve distinto para propietario, arrendatario, cooperativa y banco. Eso requiere perfiles con parámetros explícitos y marcados como supuestos, sliders validados y una vista de sensibilidad que muestre cuándo cambia el ranking, para que la herramienta no "decida" sino que exponga el trade-off.

## What Changes

- Cuatro perfiles predefinidos OWNER, TENANT, COOP y BANK con H, α, λ, i y restricciones, cada uno como supuesto `A-ACT-NN` con fuente o "pendiente AFA".
- Nivel q de la cola del Riesgo como supuesto global A-ACT-05 (lo usa rotation-engine).
- Perfiles personalizados (sliders) a partir de un perfil base, validados contra límites supuestos (A-ACT-06) y con procedencia USER_INPUT en lo modificado.
- Regla de faltante: TENANT sin arrendamiento cargado produce un Faltante.
- Requisito de demostración con test: con el lote demo existe al menos un par de actores con rankings distintos.
- Caso de uso de sensibilidad: grilla determinista sobre α o λ con el ranking en cada punto y los puntos de quiebre exactos, expuesto en `POST /api/v1/sensitivity` (api).
- Pesos opcionales de prioridades del productor (agua, N, erosión y cobertura, MO y carbono, ingreso suplementario) que re-ponderan de forma determinista los pesos w_k de ΔSuelo y agregan dos términos documentados al puntaje, sin romper la monotonicidad que verifica quality (A-ACT-07 a A-ACT-09).
- Ventanas de maquinaria disponibles (meses por operación de siembra y cosecha) como restricción explícita de entrada del productor; el motor las aplica.

## Capabilities

### New Capabilities
- `actor-profiles`: perfiles de actor predefinidos y personalizados, su validación, la garantía de rankings distintos en la demo y el análisis de sensibilidad del ranking.

### Modified Capabilities
- Ninguna.

## Impact

- Datos de perfiles en `assumptions.yaml` (valores) y un módulo puro de perfiles y sensibilidad en `fieldshift.engine` (cálculo) más un caso de uso en `fieldshift.application`.
- Consumidores: `api` (GET /api/v1/actors/profiles y POST /api/v1/sensitivity), `web-demo` (sliders, prioridades y gráfico), `whatsapp-channel` (elegir actor), `explanations`.
- Depende de `rotation-engine`, `economics`, `soil-impact` y del fixture de `demo-mode`.

## Fuera de alcance

- Agrónomo y Contratista como perfiles con parámetros propios (el agrónomo es el usuario experto; el contratista como perfil queda P2, aunque el productor ya declara sus ventanas de maquinaria).
- Aprender preferencias del usuario o elicitar α/λ con cuestionarios.
- Persistir perfiles personalizados entre sesiones.
