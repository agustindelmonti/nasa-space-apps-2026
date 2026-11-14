# Design: api

## Context

Ver proposal.md. Arquitectura en capas: `adapters.api` (FastAPI) llama a casos de uso de `application`, que resuelven la entrada desde `data` (caché parquet validada y fixtures de `demo-mode`), corren `engine` (puro) y generan `explanations`. El motor no hace I/O; la API tampoco hace red saliente durante una evaluación.

## Goals / Non-Goals

**Goals:** contrato estable y autodocumentado para `web-demo` y el simulador; errores predecibles; respuestas reproducibles byte a byte; deploy en una sola instancia gratuita.

**Non-Goals:** autenticación, persistencia, escalado horizontal, cache HTTP distribuida.

## Decisions

1. **Unión discriminada por `mode`** en `EvaluateRequest = LiteEvaluateRequest | FullEvaluateRequest`. Alternativa descartada: dos endpoints (/evaluate y /evaluate/lite): duplica documentación y lógica de respuesta; xcut fija un solo POST /evaluate.
2. **Respuesta serializada con el JSON canónico de `domain-models`** mediante una `Response` propia (`CanonicalJSONResponse`) en lugar del `JSONResponse` de FastAPI, para garantizar orden de claves, redondeo y bytes idénticos. Headers variables (`X-Request-Id`) quedan fuera del body.
3. **`EvaluateResponse`**: `{input_hash, engine_version, templates_version, engine_output, explanation, resolution, display_order, contrast_output?, robustness?}`. `resolution` es una lista ordenada de `{part, origin: USER_INPUT|CACHE|FIXTURE|ASSUMPTION|MISSING, source_ref, assumption_ids}`.
4. **Resolución lite en `application.resolve_lite_input`**: snap de lat/lon a la clave de celda de la caché según la regla de `nasa-ingestion`; perfil desde `actor-profiles`; parámetros económicos desde el archivo versionado de `economics`; suelo campo por campo desde request (USER_INPUT), luego caché SoilGrids (OBSERVED `is_modeled=true`, agua útil DERIVED con A-WAT-17), luego A-WAT-14 genérico (ASSUMPTION), registrando faltante en los dos últimos casos; nunca se descarga SoilGrids durante la evaluación. Si falta un parámetro obligatorio se lanza `MissingParameterError` (mapeado a MISSING_PARAMETER); si falta un dataset, `DataUnavailableError`.
5. **Errores**: jerarquía `ApiError(code, http_status, message, details)` con enum `ErrorCode`; handlers globales para `RequestValidationError` (VALIDATION_ERROR con `details=[{loc, msg}]` sin eco de valores), `HTTPException` 404/405 y excepciones no previstas (INTERNAL_ERROR). Test de contrato: todo `ApiError` emitido pertenece al enum, y el enum coincide con el OpenAPI.
6. **Tamaño**: middleware ASGI que lee `Content-Length` y corta el stream al superar el límite por ruta, antes de parsear. Alternativa descartada: confiar en el proxy de Render (no es configurable en plan gratuito).
7. **Rate limit**: token bucket en memoria por clave (IP de `X-Forwarded-For` confiable según config, y hash del número en el webhook), con límites por ruta desde `pydantic-settings`. Alternativa descartada: `slowapi`/Redis (dependencia extra; una sola instancia alcanza para la demo).
8. **Timeout**: el motor corre en threadpool con `asyncio.wait_for`; al vencer, se responde TIMEOUT (el hilo termina en background; el motor es puro y no deja estado). Default configurable (por ejemplo 10 s).
9. **Health**: lee un índice de caché (manifest de `nasa-ingestion`) en lugar de recorrer archivos; `status` es `ok`, `degraded` (algún dataset EMPTY o PARTIAL fuera de DEMO_MODE) o `demo`.
10. **CORS**: `CORSMiddleware` con `allow_origins` desde `CORS_ALLOWED_ORIGINS` (lista explícita), `allow_credentials=False`, métodos GET/POST/OPTIONS. Alternativa descartada: `*` (innecesario y mala práctica en repo público).
11. **Configuración**: `Settings` (`pydantic-settings`) con `SecretStr` para secretos; `repr` y `model_dump` nunca exponen valores; `.env.example` con todas las claves vacías.
12. **Comparación OWNER vs TENANT**: flag `include_owner_tenant_contrast` en el request; la aplicación corre el motor dos veces con perfiles predefinidos y devuelve `contrast_output`. El `X-Input-Hash` corresponde al actor pedido.
13. **Filtro por clase de año**: campo opcional `year_class_filter` (ALL, DRY, NORMAL, WET; ALL por defecto) en ambos modos de /evaluate y en /sensitivity. La aplicación lo copia a `EngineInput` (entra al hash) y el motor re-pondera; la API no filtra por su cuenta. Alternativa descartada: filtrar escenarios en la aplicación (quedaría fuera de la salida auditable).
14. **POST /sensitivity**: mismo `mode` lite|full que /evaluate más `parameter`, `min`, `max`, `n`. Corre el motor una vez y recombina con el caso de uso de actor-profiles; respuesta canónica con `input_hash` de la entrada base y `X-Input-Hash`. Mismo timeout y límite de tamaño que /evaluate.
15. **Lecturas de campo (P2)**: `POST/GET /plots/{plot_id}/field-readings` delegan en `application.field` (field-measurement); errores propios SESSION_CONFLICT y SAMPLING_RATE_TOO_LOW en el catálogo. Nunca tocan el motor.
16. **Preferencias de presentación**: `display_preferences ⊆ {WATER_SAFE_FIRST, DOUBLE_CROP_FIRST}` reemplazan a las ex prioridades de agua e ingreso suplementario (A-ACT-08 y A-ACT-09 retirados). La aplicación calcula `display_order` con `sorted(results, key=(grupo_agua?, no_doble?, rank))`: grupo de agua 0 = FEASIBLE, 1 = RISKY o UNKNOWN, 2 = NOT_FEASIBLE. No entran a `EngineInput`, así que el `input_hash`, el ranking y los puntajes no cambian. Web y chat usan este orden y nunca reordenan por su cuenta. Alternativa descartada: términos en el puntaje (exigían coeficientes inventados).
17. **Robustez**: `include_robustness` corre el caso de uso de actor-profiles (7 evaluaciones extra del motor puro, costo trivial con N <= 6 candidatas) dentro del mismo timeout.
18. **POST /rotation-sheet (P2), decisión POST y no GET**: la ficha depende de toda la entrada (suelo, perfil, parámetros, filtro); la API no persiste evaluaciones, así que un GET por id no tendría qué leer y un GET con la entrada en query string superaría límites de URL y rompería la canonicalización. Request = el de /evaluate (lite o full) + `rotation_id` + `format` (json | text). Respuesta canónica e idempotente con `X-Input-Hash`. Alternativas descartadas: GET /rotations/{id}/sheet con estado en memoria (rompe idempotencia entre instancias y reinicios), PDF en el servidor (no determinista).

## Risks / Trade-offs

- [Cold start de Render gratuito tarda decenas de segundos] → la demo en vivo usa DEMO_MODE y un ping previo a /health; el front muestra estado de carga.
- [Rate limit por IP detrás de proxy cuenta mal] → cabecera de IP confiable configurable; en la demo el límite es holgado.
- [Request lite con suelo faltante produce resultados poco informativos] → `resolution` y faltantes lo hacen visible; nunca se rellena en silencio.
- [Timeout corta pero el hilo sigue consumiendo CPU] → aceptado para el MVP; el motor está acotado por tamaño de entrada.

## Open Questions

- Dominio final del front para `CORS_ALLOWED_ORIGINS` (se completa en deploy).
- Límites concretos de rate limit y tamaño: se ajustan tras medir el tamaño real de la fixture `demo-casilda`.
