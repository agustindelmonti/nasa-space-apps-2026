# Capas GIBS verificadas (14/11/2026)

Verificadas contra GetCapabilities de `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/wmts.cgi` (1330 capas). Plantilla de tile: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{Layer}/default/{YYYY-MM-DD}/{TileMatrixSet}/{z}/{y}/{x}.{png|jpg}`.

| Uso en Rastrojo | Identificador | TileMatrixSet (zoom máx.) | Formato | Rango temporal (último intervalo) | Nota |
|---|---|---|---|---|---|
| NDVI histórico (cobertura) | `MODIS_Terra_NDVI_8Day` | GoogleMapsCompatible_Level9 | png | hasta 2026-11-13, diario | 250 m; a nivel lote se ve como pocos píxeles |
| NDVI alternativo | `VIIRS_SNPP_NDVI_8Day` | Level8 | png | hasta 2026-11-02 | 500 m |
| NDVI largo plazo | `MODIS_Terra_L3_NDVI_16Day`, `Landsat_WELD_NDVI_Global_Monthly` | Level9 / ver caps | png | 16 días desde 2000 / mensual | WELD es Landsat 30 m |
| Humedad zona de raíces | `SMAP_L4_Analyzed_Root_Zone_Soil_Moisture` | Level6 | png | hasta 2026-11-10 | ~9 km; también existe la capa de incertidumbre `SMAP_L4_Uncertainty_Analyzed_Root_Zone_Soil_Moisture` |
| Humedad superficial | `SMAP_L4_Analyzed_Surface_Soil_Moisture` | Level6 | png | diario | |
| Lluvia | `IMERG_Precipitation_Rate` | Level6 | png | hasta 2026-11-13 | tasa, no acumulado diario |
| Agua total (GRACE) | `GRACE_Tellus_Liquid_Water_Equivalent_Thickness_Mascon_CRI` | Level6 | png | mensual, hasta 2022-07-01 | sirve como capa visual regional; el dato numérico sale de la ingesta |
| Imagen 30 m | `HLS_S30_Nadir_BRDF_Adjusted_Reflectance`, `HLS_L30_Nadir_BRDF_Adjusted_Reflectance` | Level12 | jpg/png | hasta 2026-11-06 | cobertura por fecha irregular: en el lote demo varias fechas devuelven tiles vacíos; hay que buscar la última fecha con datos o usar el mosaico Sentinel-2 cloudless como base |
| Relieve | `SRTM_Color_Index` | Level12 | png | estático | contexto de loma/bajo (P1) |

No hay capa ECOSTRESS en el endpoint `best` EPSG:3857.
