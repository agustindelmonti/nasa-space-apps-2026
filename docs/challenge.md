# Desafío oficial: Field Shift: Adapting Farms with NASA Data

Fuente: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/ (copiado a mano por el equipo el 14/11/2026; el sitio no es accesible desde el entorno de desarrollo). Dificultad: Intermediate/Advanced. Temas: Arts & Multimedia, Earth Science, Software. Equipos inscriptos en el desafío al 14/11: **1832**.

## Summary (textual)

> Farmers around the world navigate shifting temperatures, changing rainfall patterns, water shortages, extreme weather, and declining soil health. These pressures make it difficult to choose crop rotations that protect fields, conserve water, and support long-term resilience. Your challenge is to create a decision-support tool that uses NASA Earth observations along with local soil information, crop characteristics, and farmer priorities to help farmers explore rotation strategies that could strengthen soil health and adapt their farms to changing conditions.

## Objectives (resumen fiel)

- App, modelo, mapa interactivo u otra herramienta que combine observaciones NASA con información agrícola local.
- Datasets sugeridos: SMAP, ECOSTRESS, GPM, Landsat, MODIS, NASA POWER, GRACE/GRACE-FO, SRTM u otros de elevación.
- Patrones a analizar: temperatura, **estrés térmico**, lluvia, humedad de suelo, evaporación, **riesgo de heladas**, **precipitación extrema**, estrés de vegetación, tendencias hídricas de largo plazo.
- Prioridades del productor citadas: uso de agua, **valor forrajero**, fijación de N, **reducción de erosión**, mejora de materia orgánica, **aptitud de mercado**.
- La herramienta puede resaltar **momentos en que el lote suele estar descubierto**, **estaciones en que los cultivos actuales son más vulnerables**, y oportunidades de rotación que corten ciclos de plagas, reduzcan demanda de agua, mejoren infiltración o sumen ingreso.
- Comparar al menos tres estrategias, incluida la actual. Para cada una: por qué se sugirió, qué evidencia la respalda, qué beneficios puede ofrecer, dónde hay brechas de información y qué riesgos requieren revisión local.
- Resultado buscado: herramienta de apoyo que no reemplaza el juicio del productor ni la experticia agronómica local.

## Potential Considerations (resumen)

- **Datos y condiciones:** relacionar T, humedad, lluvia, evaporación y estrés de vegetación con vulnerabilidad y salud de suelo; explicar ET, anomalías de humedad, NDVI, riesgo de helada, balance hídrico; **cómo difiere el satélite de la medición de campo y cómo combinarlos mejora la precisión**.
- **"SI", modelado y fusión de datos:** comparar enfoques de "SI" o estadísticos sobre clima y suelo históricos; resaltar transiciones estacionales, períodos de suelo desnudo y momentos de estrés; **explicar cómo el modelo interpreta la incertidumbre y dónde hace falta validación local**; **armonizar resoluciones espaciales y temporales a una grilla común** (SMAP, ECOSTRESS, GPM, Landsat/MODIS, GEDI, suelos).
- **Rotaciones:** ciclado de nutrientes, riesgo de erosión, aporte de MO, corte de plagas, uso de agua, forraje, mercado; mapear rotaciones contra prioridades; explicar el aporte de leguminosas, cultivos de servicio, raíces profundas y cultivos tolerantes a sequía.
- **Mapas y visualización:** tendencias en el tiempo (humedad, olas de calor, descenso de almacenamiento de agua); vulnerabilidades a nivel lote (erosión, estrés hídrico, zonas con heladas); timelines, overlays, **sliders de escenario de lluvia o temperatura**.
- **Diseño centrado en el productor:** interpretable sin experiencia técnica; ingreso de prioridades y restricciones propias (**agua disponible, limitaciones de maquinaria, preferencias de mercado**); recordatorios de que apoya y no reemplaza.

## Resources (tab oficial) y equivalente local que usamos o proponemos

| Recurso oficial | Tipo | Equivalente o uso en Argentina |
|---|---|---|
| SMAP | NASA | Usamos SMAP L4 (zona de raíces) |
| GPM / IMERG | NASA | Usamos IMERG Final diario |
| Landsat, MODIS/VIIRS | NASA/USGS | MODIS NDVI y HLS (Landsat + Sentinel-2) |
| NASA POWER | NASA | Base agroclimática (lluvia, T, ET0, heladas) |
| SRTM | NASA | Propuesto P1: pendiente y bajos (anegamiento) del lote |
| ECOSTRESS | NASA | Propuesto P2: LST y ET de alta resolución como evidencia |
| GRACE/GRACE-FO | NASA (Objectives) | Usamos como contexto regional de agua total |
| NLDAS/GLDAS | NASA | GLDAS (global) como alternativa a SMAP antes de 2015, P2 |
| GEDI | NASA | Poco útil en agricultura extensiva sin árboles; no lo usamos |
| USDA Ag Data Commons, WSS, SSURGO/STATSGO2 | USDA (solo EE. UU.) | Cartas de suelo INTA (GeoINTA) y SoilGrids (modelado) |
| CDL CropScape | USDA (solo EE. UU.) | MapBiomas Argentina / mapas de cultivos INTA, P2 |
| PRISM | OSU (solo EE. UU.) | Estaciones SMN / INTA como dato de campo, P2 |
| CoCoRaHS | Comunitario (Norteamérica) | Pluviómetros de socios AFA (dato de campo) |
| USGS NWIS | USGS (solo EE. UU.) | Freatímetros INTA / productor (napa) |
| USDA AMS Market News | USDA | Precios Bolsa de Comercio de Rosario (parámetro con fecha) |
| USDA NASS QuickStats | USDA | Estimaciones agrícolas MAGyP / BCR (rindes departamentales) |
| OpenET | Solo oeste de EE. UU. | No aplica; ET0 de POWER + ECOSTRESS |
| USFS LANDFIRE | Solo EE. UU. | No aplica |
| FAO GAEZ | FAO | Aptitud agroclimática como evidencia de contexto, P2 |
| Copernicus Sentinel-2 | ESA | Vía HLS |
| ERA5 | ECMWF | Alternativa de reanálisis si POWER tiene huecos, P2 |

Lectura: casi todos los recursos de suelo, cultivo, mercado y validación son de EE. UU. **Mapear cada uno a su equivalente argentino es un diferencial concreto** para el criterio de Pertinencia y para AFA.

## Notas para el pitch

- El enunciado usa "SI" donde se espera "AI". Nuestra postura: el motor es estadístico y determinista sobre escenarios históricos enumerados (explicable y auditable); la IA generativa solo reformula texto en el canal, con guardas. Explicamos la incertidumbre por la dispersión entre años secos, normales y húmedos.
- Sliders de escenario: nuestros sliders son de prioridades del actor (H, α, λ) y además podemos filtrar por clase de año (solo secos, solo húmedos), que responde al pedido de "scenario sliders" sin inventar clima.
