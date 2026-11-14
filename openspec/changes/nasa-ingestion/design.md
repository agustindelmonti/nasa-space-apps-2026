# Design: nasa-ingestion

## Context

Ver proposal.md. Depende de `domain-models` (Source, PValue, Provenance). El motor no hace I/O: esta capa (`fieldshift.data`) resuelve todo antes y la aplicación arma `EngineInput`. Hay que llegar a la demo del sábado con el lote `demo-casilda` cacheado; el acceso a Earthdata en la sede puede fallar, así que la caché y los fixtures son la fuente operativa y la descarga es un paso previo.

## Goals / Non-Goals

**Goals:** un adaptador por dataset con contrato común; caché reproducible; huecos visibles; metadatos de resolución y limitación reutilizables por explicaciones y web.

**Non-Goals:** paralelismo de descargas, procesamiento de grillas completas, servidor de datos propio, actualización automática programada.

## Decisions

1. **Contrato común de adaptador.** Cada dataset implementa `fetch(point, period) -> RawFrame` (red) y `normalize(RawFrame) -> CachedFrame` (puro). La normalización (escala, relleno a faltante, unidades) es pura y se testea con archivos de muestra sin red. Alternativa descartada: un único script por dataset sin separar red de normalización (no testeable offline).
2. **Formato de caché: parquet (pyarrow) + sidecar JSON** `<clave>.meta.json` con parámetros de consulta, versión del producto, `retrieved_at`, celda efectiva y `content_sha256` (hash de los bytes del parquet escrito con opciones fijas: sin índice de pandas, compresión `zstd` fija, columnas ordenadas). `retrieved_at` va solo en el sidecar para que el contenido sea idéntico entre corridas. Alternativas descartadas: NetCDF (más pesado de validar con pandera), SQLite (innecesario sin consultas cruzadas), CSV (pierde tipos).
3. **Clave de caché**: `data/cache/<DATASET>/<lat:.4f>_<lon:.4f>_<YYYYMMDD>-<YYYYMMDD>.parquet`. Precisión 4 decimales (~11 m) muy por debajo de cualquier resolución de los datasets.
4. **Esquemas pandera por dataset** (formato largo para series diarias: `date`, `variable`, `value`, `unit`, `is_missing`, `missing_reason`). Formato largo para que el registro de huecos sea una consulta y no una convención. Rangos físicos en el esquema (por ejemplo `sm_rootzone` 0 a 0.9, NDVI -1 a 1, T2M -40 a 60 °C).
5. **POWER vía httpx**: `GET https://power.larc.nasa.gov/api/temporal/daily/point` con `community=AG`, `parameters=PRECTOTCORR,T2M,T2M_MIN,T2M_MAX,RH2M,WS2M,ALLSKY_SFC_SW_DWN,PS` (más `CLRSKY_SFC_SW_DWN` si se necesita Rso), `format=JSON`, partido en tramos por año para no superar límites. Valor de relleno -999 a faltante. Sin credenciales.
6. **ET0**: primera tarea verifica si POWER publica una ET de referencia FAO-56 en la comunidad AG. Si existe, se usa como OBSERVED. Si no, se calcula Penman-Monteith FAO-56 diario (ecuación 6) con Rs = ALLSKY_SFC_SW_DWN, ea desde RH2M y T2M, presión PS, viento a 2 m WS2M, Rso desde radiación extraterrestre por latitud y día (o CLRSKY), G = 0. Implementación pura en `fieldshift.data.et0` con tests contra el ejemplo 18 de FAO-56. Alternativa descartada: Hargreaves (solo temperatura, menos preciso y no aprovecha radiación de POWER).
7. **Earthdata con earthaccess** (`earthaccess.login(strategy="environment")`). Para limitar volumen:
   - SMAP L4 SPL4SMGP: granulos 3-horarios grandes; se usa subsetting (OPeNDAP o Harmony) para extraer solo `sm_rootzone` en la celda; para la demo se precalcula un período acotado (por ejemplo 2015 a la fecha, o las ventanas necesarias) y se guarda como fixture.
   - GPM IMERG `GPM_3IMERGDF` (Final Run diario, V07): lectura parcial con xarray de la celda.
   - GRACE/GRACE-FO: archivo único de mascons JPL RL06.x CRI (grilla 0.5°, mascons de ~3°) en PO.DAAC; se baja una vez y se extrae la celda. CSR como alternativa documentada.
   - MOD13Q1 v061: subsetting por punto (servicio de subsets de ORNL DAAC o lectura de tile); QA "pixel reliability" > 1 se descarta.
   - HLS (P2): solo si sobra tiempo, NDVI desde B04/B05 (L30) o B04/B8A (S30) con máscara Fmask.
8. **Procedencia de productos modelados** (regla acordada en domain-models): los valores tal como los publica un tercero se emiten como OBSERVED con `is_modeled` explícito (true para SMAP L4, POWER basado en MERRA-2, mascons GRACE-FO, SoilGrids y GLDAS; false para IMERG, MODIS, SRTM y ECOSTRESS). Agregaciones, ET0 calculada, pendiente y posición en el relieve son DERIVED. Alternativa descartada: marcar todo producto modelado como DERIVED (borra la diferencia entre "lo publica NASA" y "lo calculamos nosotros", que es la que importa en el panel de evidencia).
9. **Modo offline**: un `Settings` (pydantic-settings) con `demo_mode`, `offline`, `cache_dir`, credenciales. En modo offline los adaptadores de red se reemplazan por uno que lanza `DATA_NOT_CACHED`; un test con `pytest-socket` (o monkeypatch de httpx) garantiza cero red.
10. **Errores tipados**: `PERIOD_OUT_OF_COVERAGE`, `DATA_NOT_CACHED`, `EARTHDATA_AUTH_MISSING`, `UPSTREAM_UNAVAILABLE`, `CACHE_SCHEMA_INVALID`, `SOURCE_INCOMPLETE`. La API los traduce a `{code, message, details}`.

11. **SRTM (P1)**: SRTMGL1 (30 m) vía earthaccess; se recorta una ventana de tamaño fijo alrededor del lote (por ejemplo 2 km de lado, parámetro técnico de ingesta documentado en el catálogo, no agronómico) y se calcula pendiente media en % y posición relativa por percentil de la elevación del lote dentro de la ventana (loma, media loma, bajo). Salida: Evidencia de contexto de anegamiento y erosión para explanations y web; MUST NOT entrar al motor. Alternativa descartada: índice topográfico de humedad completo (requiere dirección de flujo y más tiempo).
12. **ECOSTRESS (P2)**: LST y ET (L2/L3) para fechas con pasada sobre el lote; solo evidencia, con limitación de cobertura irregular. MUST NOT entrar al motor.
13. **Resumen NDVI mensual**: por mes calendario, mediana de NDVI y fracción de compuestos válidos con NDVI bajo el umbral A-SOIL-10, sobre todo el período disponible; es el insumo de evidencia que viaja en `EngineInput` para soil-impact.
14. **SoilGrids (P1)**: API REST `https://rest.isric.org/soilgrids/v2.0/properties/query` (sin credenciales) para las propiedades `sand`, `silt`, `clay`, `soc`, `wv0033` y `wv1500` en las capas 0-5, 5-15, 15-30, 30-60 y 60-100 cm, valor medio, con la conversión de unidades publicada por SoilGrids. Se cachea como un dataset más (parquet + sidecar). OBSERVED con `is_modeled=true` (regla de domain-models), resolución 250 m. El agua útil integrada por capa es DERIVED con A-WAT-17. Limitación en el catálogo: "modelo global de 250 m; no reemplaza la carta de suelo INTA ni un análisis del lote". La api lo usa en la resolución lite con prioridad dato del usuario > caché SoilGrids > A-WAT-14. Alternativas descartadas: GeoINTA/SISINTA (sin API estable para la sede; queda como recurso argentino a citar), descarga de rasters completos (volumen innecesario para un punto).
15. **Comparación POWER vs IMERG (P1)**: por año de campaña con ambas series completas, sumas de cada fuente (`sum_daily`), diferencia relativa respecto de POWER y fuente menor. Es evidencia para el panel ("tomamos la más conservadora") y el insumo de la regla A-WAT-16; la clasificación de años no la usa. Alternativa descartada: calcularla en climate-scenarios (ya emite la advertencia A-CLI-04 por ventana, pero la regla del balance necesita la campaña completa).

### Armonización de resoluciones (P0 documental)

El enunciado pide armonizar resoluciones a una grilla común. En el MVP no se re-grilla: cada dataset se muestrea en su resolución nativa al elemento que contiene el centroide del lote, y la Source registra la celda efectiva (coordenadas del centro y tamaño). La comparación entre datasets se hace en el dominio del lote (un punto), no en una grilla.

| Dataset | Resolución nativa | Muestreo al lote | Celda efectiva registrada |
|---|---|---|---|
| NASA_POWER | ~0.5° x 0.625° (radiación ~1°); diario | celda que contiene el punto (la API de POWER ya devuelve el punto de grilla) | centro de celda y tamaño |
| SMAP_L4 | ~9 km EASE-Grid 2.0; 3-horario | celda EASE que contiene el punto; media diaria DERIVED | índice de fila/columna y centro |
| GPM_IMERG | 0.1°; diario | celda que contiene el punto | centro de celda |
| GRACE_FO | grilla 0.5°, mascons ~3°, ~300 km efectivos; mensual | celda 0.5° que contiene el punto | centro de celda y aviso de resolución efectiva |
| MODIS_NDVI | 250 m; 16 días | píxel que contiene el punto | centro de píxel |
| HLS_NDVI (P2) | 30 m; 2 a 3 días | píxel que contiene el punto | centro de píxel |
| SRTM (P1) | 30 m; estático | ventana fija alrededor del punto para pendiente y posición | bbox de la ventana |
| SOILGRIDS (P1) | 250 m; estático por capa | píxel que contiene el punto | centro de píxel y capas |
| ECOSTRESS (P2) | ~70 m; irregular | píxel que contiene el punto por pasada | centro de píxel y fecha de pasada |

Temporalmente, todo se lleva a paso diario o a ventanas de campaña con agregaciones DERIVED explícitas (media diaria de SMAP, acumulados por ventana, resumen NDVI mensual); GRACE-FO queda mensual. Alternativa descartada: re-grillar todo a 0.1° con interpolación (agrega números que ningún dataset publicó y esconde la diferencia de escala que queremos mostrar).

### Metadatos por dataset (catálogo inicial, verificar versiones al implementar)

| Dataset | Producto / variable | Resolución | Cobertura | Limitación en lenguaje simple |
|---|---|---|---|---|
| NASA_POWER | daily point AG: PRECTOTCORR, T2M, T2M_MIN, T2M_MAX, RH2M, WS2M, ALLSKY_SFC_SW_DWN, PS | ~0.5° x 0.625° meteorología, ~1° radiación; diario | 1981+ (radiación desde 1984) | Promedio de una celda de decenas de km; lluvia de reanálisis corregida, no pluviómetro del lote |
| SMAP_L4 | SPL4SMGP `sm_rootzone` | ~9 km; 3-horario | 2015-03-31+ | Modelo con asimilación satelital; 0 a 100 cm, no distingue lotes vecinos |
| GPM_IMERG | GPM_3IMERGDF precipitación | 0.1°; diario | 2000-06+ (V07 extiende hacia atrás) | Estimación satelital; puede errar en tormentas convectivas localizadas |
| GRACE_FO | Mascons JPL RL06.x CRI, TWS anomaly | ~300 km efectivos; mensual | 2002-04+ con hueco 2017-07 a 2018-05 y meses sueltos | Regional: dice si la región está más seca o húmeda que su línea base, no el lote |
| MODIS_NDVI | MOD13Q1 v061 NDVI | 250 m; 16 días | 2000-02+ | Mezcla lote y bordes; nubes generan huecos |
| HLS_NDVI (P2) | HLSL30/HLSS30 v2.0 | 30 m; 2 a 3 días combinado | 2013+/2015+ | Muchas nubes en invierno; volumen grande |
| SOILGRIDS (P1) | SoilGrids 2.0: sand, silt, clay, soc, wv0033, wv1500 por capa | 250 m; estático | producto global (versión a verificar) | Modelo global de aprendizaje automático; no reemplaza la carta de suelo INTA ni un análisis del lote |
| SRTM (P1) | SRTMGL1 v003 elevación | 30 m; estático | 2000 (misión única) | Elevación de 2000; en llanura plana las diferencias son de pocos metros y el error vertical pesa |
| ECOSTRESS (P2) | ECO L2 LST / L3 ET | ~70 m; pasadas irregulares | 2018-07+ | Horario de pasada variable y huecos; no es serie diaria |

## Risks / Trade-offs

- [Earthdata o red de la sede caídos] → fixtures del lote de demo commiteados en `data/fixtures/demo/` (tamaño acotado) y modo offline por defecto en la demo.
- [Volumen de SMAP L4] → subsetting y período acotado para la demo; documentar el comando para ampliar.
- [Cambios de versión de producto] → versión en Source y en la clave del sidecar; si cambia, se invalida la caché.
- [ET0 calculada distinta de otras referencias] → test contra ejemplo FAO-56 y método declarado en la procedencia.
- [Celda POWER grande frente al lote] → se muestra la celda efectiva y la limitación en el panel de evidencia.
- [Lectura de productos modelados como "medidos"] → OBSERVED con `is_modeled=true` (regla de domain-models) y limitación visible en el panel de evidencia.

## Supuestos abiertos para AFA

- A-WAT-17 (profundidad y método para integrar el agua útil desde SoilGrids) es el único supuesto de esta capability.
- Ninguno otro numérico: la ingesta no introduce valores agronómicos. Para AFA: qué tan representativa es una celda POWER/SMAP del sur de Santa Fe frente a sus pluviómetros y si pueden compartir registros de lluvia para contrastar (fuera del MVP).

## Open Questions

- ¿POWER publica ET0 FAO-56 en la comunidad AG para el endpoint diario? Se resuelve en la tarea 2.1; el spec cubre ambos caminos.
- Versión exacta de los mascons GRACE-FO a usar (JPL RL06.1 o RL06.3) y su short name en PO.DAAC.
- Servicio de subset para MOD13Q1 (ORNL o lectura de tile), según qué funcione desde la red de la sede.
