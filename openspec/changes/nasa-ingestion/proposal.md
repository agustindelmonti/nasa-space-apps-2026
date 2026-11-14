# Proposal: nasa-ingestion

**Prioridad:** P0 para POWER, SMAP L4 y GRACE-FO del lote de demo (sábado) y para documentar la armonización de resoluciones; P0 también MODIS NDVI del lote demo (evidencia del calendario de suelo desnudo); P1 para GPM IMERG, comparación de lluvia POWER vs IMERG, SoilGrids y SRTM; P2 para HLS y ECOSTRESS.

## Why

El criterio "Pertinencia" pide uso profundo y central de datos NASA, y el motor determinista no puede hacer I/O. Hace falta una capa que baje, valide, cachee y describa cada dataset (con resolución, período y limitación), para que la aplicación arme entradas del motor ya resueltas, la demo funcione sin internet y ningún número aparezca sin fuente ni huecos escondidos.

## What Changes

- Se define la ingesta por punto (lat/lon) y período de cinco fuentes: NASA POWER (diario, desde 1981), SMAP L4 SPL4SMGP (humedad zona de raíces, desde 2015), GPM IMERG Final Run diario (desde 2000), GRACE/GRACE-FO mascons (anomalía de TWS mensual) y MODIS MOD13Q1 NDVI (y opcionalmente HLS).
- Se define una caché local en parquet por dataset, punto y período, validada por esquema, idempotente y legible sin red.
- Se define el manejo explícito de huecos: valores de relleno y faltantes quedan registrados como faltantes, nunca interpolados en silencio.
- Se define un catálogo de metadatos por dataset (resolución espacial y temporal, cobertura, latencia, si es modelado, limitación en lenguaje simple).
- Se definen agregaciones (media diaria desde 3-horario, acumulados por ventana, totales anuales, estadísticas de NDVI por ventana y resumen NDVI mensual del lote para `EngineInput`) como valores DERIVED con insumos y método.
- Comparación de lluvia POWER vs IMERG por año de campaña (P1): sumas de ambas, diferencia relativa y cuál es la más baja, como evidencia DERIVED para el panel y como insumo de la regla conservadora de water-feasibility.
- SoilGrids (P1): textura, carbono orgánico y contenido de agua a capacidad de campo y marchitez por capa vía la API REST de SoilGrids, OBSERVED con `is_modeled=true` a 250 m, más el agua útil integrada por capa (DERIVED, A-WAT-17). Limitación: modelado global, no reemplaza la carta de suelo INTA.
- SRTM (P1): pendiente y posición relativa en el relieve (loma, media loma, bajo) del lote como evidencia de contexto de anegamiento y erosión, sin entrar al motor.
- ECOSTRESS (P2): LST y ET de alta resolución como evidencia de estrés, sin entrar al motor.
- Se documenta la armonización de resoluciones: cada dataset se muestrea al punto o celda que contiene el lote, sin re-grillar en el MVP, y se registra la celda efectiva.
- Se define la carga de credenciales Earthdata desde `.env` y un modo offline que solo lee caché.

## Capabilities

### New Capabilities
- `nasa-ingestion`: descarga, validación, caché, huecos, metadatos y agregaciones de datasets NASA por punto, con procedencia completa por registro.

### Modified Capabilities
- Ninguna. Usa los modelos de `domain-models` (Source, PValue, Provenance) sin cambiar sus requisitos.

## Impact

- Paquete `rastrojo.data` (ingesta y caché); lo consume `rastrojo.application` y el endpoint `GET /api/v1/plots/{id}/context`.
- Archivos: `data/cache/<dataset>/...parquet` (+ metadatos), `data/fixtures/demo/` para el lote de demo, `.env.example` con variables de Earthdata.
- Dependencias: `httpx`, `earthaccess`, `xarray`, `h5netcdf`/`netCDF4`, `pandas`, `pandera`, `pyarrow`, `pydantic-settings`.
- Contrato con `climate-scenarios` y `water-feasibility`: series diarias y agregados con huecos explícitos.

## Fuera de alcance

- Datasets no listados (Landsat crudo, GEDI): pueden sumarse después con el mismo contrato. GLDAS como alternativa a SMAP antes de 2015 queda P2 futuro (Source ya admite `GLDAS`).
- Re-grillado a una grilla común o fusión espacial entre datasets.
- Procesamiento de polígonos completos o promedios sobre el lote: el MVP trabaja por punto (centroide del lote).
- Pronósticos o datos en tiempo casi real con garantías de latencia.
- Relleno de huecos por interpolación, reanálisis propios o fusión estadística entre datasets.
- Servir tiles de mapa: la web usa GIBS WMTS directamente.
