# Tasks: nasa-ingestion

## 1. Base de la capa de datos (P0)

- [ ] 1.1 Crear `Settings` (pydantic-settings) con `cache_dir`, `demo_mode`, `offline` y credenciales Earthdata, y `.env.example` sin valores; verificar con un test que carga `.env.example` y que el `repr` no muestra secretos
- [ ] 1.2 Definir esquemas pandera en formato largo (`date`, `variable`, `value`, `unit`, `is_missing`, `missing_reason`) y rangos físicos por dataset; verificar con tests de "Caché corrupta" y "Rango físico fuera de lo plausible"
- [ ] 1.3 Implementar caché parquet + sidecar con clave normalizada a 4 decimales y `content_sha256`; verificar con tests de "Coordenadas equivalentes" y escritura doble con hash idéntico
- [ ] 1.4 Implementar registro de huecos y errores tipados (`PERIOD_OUT_OF_COVERAGE`, `DATA_NOT_CACHED`, `EARTHDATA_AUTH_MISSING`, `CACHE_SCHEMA_INVALID`, `SOURCE_INCOMPLETE`); verificar con test de "Source incompleta bloqueada"
- [ ] 1.5 Implementar modo offline que bloquea red; verificar con test que usa `pytest-socket` (o monkeypatch de httpx) y escenario "Faltante en modo offline"

## 2. NASA POWER y ET0 (P0)

- [ ] 2.1 Verificar en la documentación/API de POWER si existe ET0 FAO-56 diaria en la comunidad AG y anotar el resultado en design.md (Open Questions); verificación: nota commiteada con la URL consultada
- [ ] 2.2 Implementar adaptador POWER (httpx, tramos por año, relleno -999 a faltante) con normalización pura; verificar con test sobre un JSON de muestra guardado en `tests/fixtures/power/` (escenarios "Valor de relleno de POWER" y "Período anterior a 1981 rechazado")
- [ ] 2.3 Implementar ET0 Penman-Monteith FAO-56 pura (si 2.1 da negativo) o mapeo OBSERVED (si da positivo); verificar con test contra el ejemplo 18 de FAO-56 (tolerancia 0.1 mm/día) y escenario "ET0 con insumo faltante"
- [ ] 2.4 Ingestar POWER 1981 a la fecha para `demo-casilda` y guardarlo en `data/fixtures/demo/`; verificar con `uv run python -m fieldshift.data.cli ingest power --plot demo-casilda` y una segunda corrida sin red con el mismo hash

## 3. SMAP L4 y GRACE-FO (P0)

- [ ] 3.1 Implementar login earthaccess por entorno y error `EARTHDATA_AUTH_MISSING`; verificar con test sin variables de entorno (escenario "Falta de credenciales") y test de "Secretos fuera de logs"
- [ ] 3.2 Implementar adaptador SMAP L4 `sm_rootzone` con subsetting por celda y media diaria DERIVED; verificar con test sobre un subset de muestra (escenarios "Media diaria desde 3-horario" y "Día SMAP incompleto")
- [ ] 3.3 Implementar adaptador GRACE/GRACE-FO mascons con hueco entre misiones como `MISSION_GAP`; verificar con test sobre una serie de muestra 2016-2019
- [ ] 3.4 Generar fixtures SMAP y GRACE-FO del lote de demo; verificar con lectura en `DEMO_MODE=1` sin red

## 4. GPM IMERG y NDVI (P1 para IMERG; P0 para NDVI, que es evidencia del calendario de suelo desnudo)

- [ ] 4.1 Implementar adaptador IMERG Final Run diario con versión en Source y faltantes `NOT_YET_PUBLISHED`; verificar con test sobre un subset de muestra
- [ ] 4.2 Implementar adaptador MOD13Q1 con escala y filtro QA; verificar con tests "Píxel nublado" y "Escala aplicada"
- [ ] 4.3 Generar fixtures IMERG y NDVI del lote de demo; verificar lectura offline

## 5. Agregaciones, catálogo y contexto (P0 para 5.1, 5.2, 5.4 y 5.5; P1 para 5.3)

- [ ] 5.1 Implementar agregaciones DERIVED (acumulado por ventana, total anual, media diaria, estadísticos de NDVI por ventana) con conteo de usados/faltantes; verificar con tests "Acumulado de ventana con huecos" y "Acumulado completo"
- [ ] 5.2 Implementar catálogo de metadatos por dataset con resolución y limitación; verificar con test "Consulta de limitaciones"
- [ ] 5.3 Exponer a la aplicación un caso de uso `get_plot_context(plot)` que arma las series con procedencia para `GET /api/v1/plots/{id}/context`; verificar con test de integración en `DEMO_MODE=1` (escenario "Demo sin internet")

- [ ] 5.4 Documentar en el catálogo la regla de muestreo al lote y registrar la celda efectiva con su tamaño en cada Source; verificar con test "Celdas de distinto tamaño"
- [ ] 5.5 Implementar el resumen NDVI mensual del lote para `EngineInput`; verificar con test "Mes sin compuestos válidos"

## 6. SRTM (P1)

- [ ] 6.1 Implementar adaptador SRTM con ventana fija, pendiente media y posición relativa como evidencia; verificar con tests "Lote en un bajo" y "Relieve fuera del motor" sobre un recorte de muestra

## 7. HLS y ECOSTRESS (P2)

- [ ] 7.1 Implementar adaptador HLS NDVI con Fmask bajo el mismo contrato; verificar con test sobre un recorte de muestra
- [ ] 7.2 Implementar adaptador ECOSTRESS LST/ET solo como evidencia; verificar con tests "Pasada con nubes" y "ECOSTRESS fuera del motor" sobre un recorte de muestra
