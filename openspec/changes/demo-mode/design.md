# Design: demo-mode

## Context

Ver proposal.md. La ingesta (`nasa-ingestion`) escribe caché parquet validada en `data/cache/<dataset>/<lat>_<lon>_<period>.parquet`; la aplicación arma el `EngineInput` desde caché y el motor es puro. Este change agrega una fuente de datos alternativa (fixtures versionados) y la operación de la demo. Restricción del config: repo público sin secretos, nada de datos agronómicos o económicos inventados sin marcar.

## Goals / Non-Goals

**Goals:** demo idéntica con o sin internet; fixtures trazables y regenerables con un comando; detección automática de regresiones en la salida que se va a mostrar; checklist que se corre en 1 minuto antes de subir al escenario; guion y plan B ensayables.

**Non-Goals:** caché multi-lote offline, tiles GIBS propios, edición del video.

## Decisions

1. **Fixtures = caché de `nasa-ingestion` copiada a `data/fixtures/demo/`** con el mismo formato parquet y esquema pandera, más `manifest.json`. Alternativa descartada: JSON a mano o CSV propio (duplica validación y se desincroniza del formato real).
2. **Selección de fuente por configuración**: `Settings.demo_mode` (pydantic-settings, env `DEMO_MODE`). Con `True`, la aplicación inyecta un `FixtureDataSource` en lugar del cliente de red (mismo puerto/interfaz que `nasa-ingestion`). Los clientes de red, Twilio y LLM no se instancian; sus credenciales son opcionales en `Settings` cuando `demo_mode` es verdadero. Alternativa descartada: mockear httpx en runtime (frágil, oculta errores).
3. **Sin red verificable**: test con `pytest-socket` (o monkeypatch de `socket.socket.connect`) que bloquea conexiones salientes y corre el flujo `/evaluate` + `/chat/simulate` en DEMO_MODE.
4. **Lote demo**: `demo-casilda`, ubicación placeholder ejemplo lat -33.05, lon -61.15 (zona Casilda, sur de Santa Fe), superficie ejemplo 100 ha, todo ASSUMPTION `A-FLD-01` en `assumptions.yaml` con `validation_status: PENDING_AFA`. Suelo demo: campos como USER_INPUT de ejemplo o DERIVED de SoilGrids si `nasa-ingestion`/soil lo cachea; los faltantes quedan faltantes (se muestran en la demo a propósito).
5. **Parámetros económicos de ejemplo** en `data/fixtures/demo/economics.example.yaml`, cada valor con `assumption_id` `A-ECO-NN`, fuente (por ejemplo publicaciones de márgenes brutos de bolsas o revistas del sector, a completar por el responsable de `economics`) y fecha. El sufijo `.example` y un campo `is_example: true` se propagan a la respuesta de la API.
6. **Regeneración**: `uv run python -m fieldshift.scripts.refresh_demo_fixtures` (alias `make demo-fixtures`). Descarga con los clientes de `nasa-ingestion` a un directorio temporal, valida, compara con los fixtures actuales (archivos, filas, min/max/media por variable), escribe reporte Markdown en stdout y solo reemplaza si todo valida. También descarga imágenes GIBS del lote vía WMS `GetMap` (bbox del entorno del lote, fecha fija) a `data/fixtures/demo/layers/` con JSON de metadatos, que el front sirve como estáticos. Alternativa descartada: regenerar en CI (requiere secretos en CI y red; innecesario en un hackathon).
7. **Snapshot del motor**: `tests/snapshots/demo/<ACTOR>.json` con la salida canónica de `domain-models`. Actualización explícita con `--snapshot-update` (syrupy o comparación propia). El test también registra en un reporte si OWNER y TENANT difieren en orden, porque el guion depende de eso.
8. **Pre-demo**: `uv run python -m fieldshift.scripts.predemo [--local-only]` (alias `make predemo`). Ítems: health local y remoto, `demo_mode` en health, verificación de manifiesto y checksums, test de snapshot, GET del front desplegado (200 y título), `/chat/simulate` con "hola", un tile GIBS del lote, existencia de `docs/demo/backup-video.mp4` o ruta configurada. Timeout por ítem (ejemplo 5 s). Críticos: API (local o remota), fixtures, snapshot. Salida en tabla y código de salida. Además sirve para despertar la API gratuita antes del pitch.
9. **Guion** en `docs/demo/script.md` con tabla de bloques (propuesta de tiempos, ajustable en ensayo):

   | # | Bloque | Tiempo | Qué se muestra |
   |---|---|---|---|
   | 1 | Problema | 0:00-0:30 | Soja continua, agua y decisión por actor |
   | 2 | Lote en mapa con capas NASA | 0:30-1:05 | Mapa, NDVI MODIS y fecha, leyenda con resolución |
   | 3 | Agua invisible | 1:05-1:45 | SMAP L4 + IMERG en el mapa, GRACE-FO regional en evidencia, factibilidad del doble cultivo |
   | 4 | Ranking propietario vs arrendatario | 1:45-2:30 | Selector OWNER → TENANT, indicador de cambio, slider λ |
   | 5 | Evidencia y faltantes | 2:30-3:00 | Badges, tooltip de un supuesto A-..., faltante de napa |
   | 6 | WhatsApp | 3:00-3:25 | Simulador o Twilio Sandbox real |
   | 7 | Cierre honesto y visión | 3:25-3:55 | Limitaciones, supuestos AFA, uso de IA, PolPilot Agro como visión |

   Se deja un margen de 5 s. Un test simple (pytest) parsea la tabla y verifica orden y total <= 4:00.
10. **Plan B** en `docs/demo/plan-b.md`: árbol de decisión con disparadores (front público no carga en 10 s; API remota sin health; sin red) y acciones (local con `DEMO_MODE=1 uv run uvicorn ...` + `npm run preview`; video). Video grabado del flujo completo en local con DEMO_MODE, guardado offline en la notebook de presentación y en un pendrive.
11. **Material de video** en `docs/demo/video.md`: guion, lista de tomas, textos en pantalla, créditos NASA (nombres oficiales de POWER, SMAP L4, GPM IMERG, GRACE-FO, MODIS, GIBS), librerías OSS y declaración de IA.

## Risks / Trade-offs

- [Fixtures grandes en el repo] → recortar al punto/entorno del lote y al período usado; parquet comprimido; límite orientativo de pocos MB por dataset.
- [Earthdata caído al regenerar el sábado] → regenerar temprano (viernes noche o sábado mañana) y commitear; la regeneración es idempotente.
- [La demo muestra rankings iguales para propietario y arrendatario] → el snapshot lo detecta y el pre-demo lo advierte; se revisa el perfil (supuestos A-ACT) o el guion, nunca se "ajustan" datos.
- [Parámetros de ejemplo leídos como recomendación] → rótulo "ejemplo" en API, front y guion.
- [Coordenadas placeholder de un campo privado] → usar un punto genérico de zona rural sin identificar propietario; reemplazar solo con permiso.

## Migration Plan

No hay migración. Rollback: volver a la versión anterior de `data/fixtures/demo/` y snapshots vía git.

## Supuestos abiertos para AFA

- `A-FLD-01`: lote real representativo de socios para la demo (ubicación, superficie, rotación actual).
- `A-ECO-NN`: rangos de precio, costo y rinde de ejemplo razonables para la zona.

## Open Questions

- Duración exacta del video según bases de NASA Space Apps 2026 (se ajusta en `docs/demo/video.md`, no cambia specs).
- Quién presenta cada bloque (se completa en el guion).
