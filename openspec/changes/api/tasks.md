# Tasks: api

## 1. Esqueleto y errores (P0)

- [ ] 1.1 Crear app FastAPI con router `/api/v1`, `Settings` con `pydantic-settings` y `.env.example`; verificar `uv run uvicorn rastrojo.adapters.api.main:app` y GET /api/v1/health 200 con TestClient
- [ ] 1.2 Implementar `ErrorCode`, `ApiError` y handlers globales (validación, 404, 405, 500); tests "Campo extra en request", "Ruta inexistente" y "Error interno sin traza" en verde
- [ ] 1.3 Implementar `CanonicalJSONResponse` con el JSON canónico de dominio; test que compara bytes con `canonical_json(model)` en verde

## 2. Evaluación (P0)

- [ ] 2.1 Modelos `EvaluateRequest` (unión por `mode`), `EvaluateResponse` y `ResolutionEntry`; test de esquema que rechaza `mode` desconocido en verde
- [ ] 2.2 POST /evaluate modo full contra la fixture `demo-casilda`; test "EngineInput válido" en verde
- [ ] 2.3 Caso de uso `resolve_lite_input` (celda de caché, perfil, parámetros, suelo, faltantes); tests "Lite en el lote de demo", "Suelo no informado", "Actor desconocido" y "Rotación desconocida" en verde (P0, suelo con usuario > A-WAT-14)
- [ ] 2.4 Errores de cobertura y parámetros; tests "Coordenada fuera de Argentina", "Celda sin caché" y "Precio de maíz ausente" en verde
- [ ] 2.5 Headers `X-Input-Hash` y `X-Engine-Version`; tests "Dos requests iguales" y "Orden de claves distinto" en verde
- [ ] 2.6 `explanation_formats` y contraste OWNER vs TENANT; test "Solo WhatsApp" y test de `contrast_output` presente en verde

## 3. Catálogos y health (P0)

- [ ] 3.1 GET /rotations/catalog y GET /actors/profiles; tests "Catálogo estable" y "Perfiles con supuestos" en verde
- [ ] 3.2 GET /health con manifest de caché; test "Health con caché vacía" y health en DEMO_MODE en verde
- [ ] 3.3 CORS desde configuración; tests "Origen permitido" y "Origen desconocido" en verde

## 4. Contexto, glosario y supuestos (P1)

- [ ] 4.1 GET /plots/{plot_id}/context desde caché o fixtures; tests "Contexto del lote de demo" y "Lote inexistente" en verde
- [ ] 4.2 GET /glossary y GET /assumptions; test "Supuestos pendientes visibles" en verde

## 5. Protección y contrato (P1)

- [ ] 5.1 Middleware de tamaño por ruta y validación de content type; tests "Body excedido" y "Evaluate con form" en verde
- [ ] 5.2 Rate limit token bucket para /whatsapp/webhook y /chat/simulate; test "Ráfaga de requests" con reloj inyectado en verde
- [ ] 5.3 Timeout de evaluación en threadpool; test "Evaluación lenta" con motor falso en verde
- [ ] 5.4 OpenAPI con ejemplos y enum de errores; tests "Esquema exportable", "Catálogo publicado" y "Código fuera de catálogo" en verde
- [ ] 5.5 Test "Escaneo de secretos" recorriendo todos los endpoints en verde

## 6. Deploy y métricas (P2)

- [ ] 6.1 Deploy en Render o Fly con variables de entorno; verificar `curl <url>/api/v1/health` 200 y `X-Engine-Version` presente en /evaluate
- [ ] 6.2 Log de latencia por endpoint sin datos personales; verificar en logs locales una línea por request con ruta, estado y duración

## 7. Sensibilidad, filtro, suelo SoilGrids, preferencias y robustez (P1)

- [ ] 7.1 POST /sensitivity con unión por `mode` y caso de uso de actor-profiles; tests "Sensibilidad sobre λ", "Grilla inválida por HTTP" y "Sensibilidad idempotente" en verde
- [ ] 7.2 Campo `year_class_filter` (ALL, DRY, NORMAL, WET) en /evaluate y /sensitivity copiado a `EngineInput` y código EMPTY_YEAR_CLASS; tests "Ranking solo con años secos", "Valor de filtro inválido" y "Clase sin años" en verde
- [ ] 7.3 Resolución de suelo con caché SoilGrids entre el dato del usuario y A-WAT-14, con faltante; tests "Usuario manda agua útil" y "Agua útil desde SoilGrids" en verde
- [ ] 7.4 `display_preferences` y `display_order` en /evaluate fuera de `EngineInput`; tests "Primero las no riesgosas en agua", "Primero las de doble cultivo" y "Preferencia desconocida" en verde
- [ ] 7.5 `include_robustness` en /evaluate con el caso de uso de actor-profiles; test "Robustez pedida" en verde

## 8. Lecturas de campo (P2)

- [ ] 8.1 Rutas POST/GET /plots/{plot_id}/field-readings delegando en field-measurement, con SESSION_CONFLICT y SAMPLING_RATE_TOO_LOW en el catálogo; tests "Conflicto de sesión" y "Listado de sesiones" en verde y test de contrato de errores actualizado

## 9. Ficha de rotación (P2)

- [ ] 9.1 POST /rotation-sheet con unión por `mode`, `rotation_id` y `format`, delegando en `export_sheet` de explanations; tests "Ficha del lote demo", "Rotación fuera de las candidatas" y "Ficha idempotente" en verde y OpenAPI actualizado

## Agente (P1)

- [ ] A.1 Implementar POST /api/v1/ask sobre el contrato de `ask-agent` con rate limit; tests de contrato para modo por reglas y texto vacío
