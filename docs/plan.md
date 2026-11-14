# Plan de implementación

Horarios en hora de Rosario (UTC-3). **La demo en vivo es el domingo** (pitch de 4 minutos después de las 16:00). El sábado a las 19:00 es un checkpoint interno: el flujo de punta a punta tiene que andar (lote demo → datos NASA → ranking por actor con evidencia → web con mapa GIBS y chat simulado) para dedicar la noche y la mañana del domingo a P1, pulido y video. Domingo: congelamiento 13:00, GitHub verificado 15:00, ensayo 15:00–16:00, pitch después de las 16:00.

Regla de recorte: a las 16:30 se revisa el estado; lo que no esté en verde para P0 se recorta según la columna "Si atrasa".

## Cuatro carriles en paralelo

| Carril | Changes | Dueño sugerido |
|---|---|---|
| A. Motor | domain-models, climate-scenarios, water-feasibility, soil-impact, economics, rotation-engine, actor-profiles, quality (núcleo) | Claude Code + 1 dev backend |
| B. Datos | nasa-ingestion, demo-mode (fixtures) | 1 dev (necesita cuenta Earthdata) |
| C. API y textos | api, explanations, ask-agent-scripted, whatsapp-channel | 1 dev backend |
| D. Web | web-demo (contra el JSON Schema del contrato, con fixture mientras no hay API) | 1 dev frontend |

El contrato que desacopla carriles es el JSON Schema de `EngineInput`/`EngineOutput` y de `/ask` (exportado en la primera hora). D trabaja contra un `engine_output.demo.json` de ejemplo hasta que C exponga la API.

## Sábado

| Hora | A. Motor | B. Datos | C. API y textos | D. Web | Si atrasa |
|---|---|---|---|---|---|
| 10:15–11:00 | Scaffolding `uv`, modelos de dominio núcleo, JSON canónico, hash, export de schemas | Script POWER 1981–2025 para el lote demo → parquet validado | FastAPI esqueleto, `/health`, formato de errores | Vite + React + tokens de DESIGN.md + fuentes + layout de 12 columnas | — |
| 11:00–13:00 | Clasificación de años (terciles), economía con parámetros A-DEMO, balance hídrico bucket, índice de suelo, objetivo y ranking, snapshot del lote demo | ET0 FAO-56 desde POWER con test; SMAP L4 y GRACE-FO por earthaccess (o valores de fixture marcados si falla la cuenta) | Plantillas de explicación (5 secciones, glosario, leyendas) con test de anclaje de números | Mapa Leaflet con GIBS + Sentinel-2 base, contorno del lote, selector de capas; ranking con franja contra fixture | GRACE-FO solo como capa GIBS visual |
| 13:00–14:00 | Almuerzo | | | | |
| 14:00–16:30 | Perfiles de actor y sensibilidad; property tests de monotonicidad; determinismo en 2 procesos | IMERG (cruce) y NDVI mensual; fixtures completos en `data/fixtures/demo/`; manifiesto con checksums | `/evaluate` (full y lite), `/rotations/catalog`, `/actors/profiles`, `/plots/{id}/context`, `/glossary`, `/assumptions` | Selector de actor + sliders contra la API, reordenamiento FLIP con ▲▼, panel Agua invisible, evidencia y badges | Sliders solo con perfiles predefinidos |
| 16:30 | **Checkpoint de recorte** | | | | |
| 16:30–19:00 | Calendarios de suelo desnudo y vulnerabilidad; años con pérdida | `DEMO_MODE=1` sin red verificado | Agente por reglas con 3 intenciones (ranking, por qué, agua) y `/ask`; `/chat/simulate` | Panel de chat + simulador WhatsApp; leyendas; deploy Vercel | Chat solo con menú |
| 19:00 | **Checkpoint interno: flujo de punta a punta andando**, deploy API en Render, comando `predemo` | | | | |
| 19:00–23:00 | Robustez del ranking, franjas de 24 meses, años con pérdida en UI | Regenerar fixtures con datos reales si faltó algo; SRTM (P1) | Agente por reglas completo; WhatsApp Twilio sandbox; POWER vs IMERG en evidencia | Calendarios en la UI; animaciones restantes; `impeccable detect` y `critique` | — |

## Domingo

| Hora | Qué |
|---|---|
| 08:30–11:00 | P1: robustez del ranking, POWER vs IMERG, ficha (si hay tiempo), field-measurement (P2), ask-agent-llm (P2) |
| 11:00–12:00 | Video (variante 30 s y 4 min según bases), capturas, página NASA |
| 12:00–13:00 | README final, AI_USE, PRIOR_WORK, licencias, `impeccable polish`, `predemo` en verde |
| 13:00 | Congelamiento de código |
| 15:00 | Todo en GitHub y verificado |
| 15:00–16:00 | Ensayo final del pitch con demo en vivo |
| Después de 16:00 | **Pitch y demo en vivo** (4 min). Plan B: `DEMO_MODE=1` local y video |

## Definición del checkpoint de punta a punta (sábado 19:00)

1. Abrir la web desplegada, ver el lote demo sobre imagen real con capa SMAP de GIBS.
2. Ver al menos 3 rotaciones (incluida la actual) con puntaje, estado hídrico, ΔSuelo y franja.
3. Cambiar de Propietario a Arrendatario y ver que el ranking cambia.
4. Abrir evidencia de una rotación con dataset, período y procedencia.
5. Preguntar en el chat "¿por qué sale primera?" y recibir la explicación.
6. Todo lo anterior también con `DEMO_MODE=1` sin red.

## Bloqueantes conocidos

- Cuenta NASA Earthdata del equipo para SMAP, IMERG y GRACE-FO (se pide por el formulario seguro de credenciales cuando arranque el carril B).
- Coordenadas reales del lote demo (hoy: parcela de ejemplo al sureste de Casilda, A-DEMO-01).
- Parámetros económicos de ejemplo con fuente y fecha (A-DEMO-02..06): idealmente validados con AFA hoy.
- Reglas oficiales del video (¿30 s?) a confirmar con el Local Lead.
