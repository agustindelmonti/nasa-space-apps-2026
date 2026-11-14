# Design: web-demo

## Context

Ver proposal.md. La API (change `api`) expone `/api/v1` con los endpoints de xcut; el motor es determinista y vive en Python. El front se escribe desde cero durante el evento, se despliega en Vercel (plan gratuito) y tiene que andar proyectado en la sede y desde el celular del jurado. La red de la sede es incierta: el modo demo (change `demo-mode`) garantiza la API sin red externa, y este front solo agrega tiles GIBS.

## Goals / Non-Goals

**Goals:** una sola página clara para el pitch de 4 minutos; capas NASA reales con fecha, leyenda y limitación; ranking por actor que cambia en vivo; procedencia visible en cada número; cero lógica de motor en el navegador; tests E2E con Playwright.

**Non-Goals:** SSR, router multi-página, gestión de estado global compleja, edición de lotes, offline completo (PWA), i18n.

## Decisions

1. **Vite + React + TypeScript, SPA estática en Vercel.** Alternativas descartadas: Next.js (SSR innecesario, más superficie de deploy); Streamlit/Dash (rápido para Python pero sin control fino de mapa, accesibilidad ni look de pitch, y obliga a hostear un server para el front).
2. **Leaflet + react-leaflet con WMTS de GIBS en EPSG:3857** vía `L.tileLayer` con plantilla REST: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{layer}/default/{time}/{tileMatrixSet}/{z}/{y}/{x}.{ext}`. Alternativas descartadas: MapLibre/OpenLayers (más potentes, más curva para el equipo); EPSG:4326 (Leaflet necesita plugin Proj4Leaflet).
3. **Catálogo de capas en configuración versionada** (`web/src/config/layers.json`): id GIBS, nombre, tileMatrixSet, nivel máximo de zoom, formato, granularidad temporal (diaria, 8 días, 16 días), rango de fechas, leyenda (colores y unidad), resolución espacial y temporal, limitación y término de glosario. Propuesta inicial, **identificadores a verificar contra GetCapabilities de GIBS** (tarea 2.1):

   | Capa | Identificador GIBS propuesto | Matriz | Notas |
   |---|---|---|---|
   | Base | `VIIRS_SNPP_CorrectedReflectance_TrueColor` o `MODIS_Terra_CorrectedReflectance_TrueColor` | `GoogleMapsCompatible_Level9` | jpg, diaria |
   | NDVI | `MODIS_Terra_NDVI_8Day` (alternativa `MODIS_Terra_L3_NDVI_16Day`) | `GoogleMapsCompatible_Level9` | png, ~250 m |
   | Humedad de suelo | `SMAP_L4_Analyzed_Root_Zone_Soil_Moisture` (alternativa `SMAP_L4_Analyzed_Surface_Soil_Moisture`) | `GoogleMapsCompatible_Level6` | png, ~9 km, modelado |
   | Precipitación | `IMERG_Precipitation_Rate` (verificar si hay variante diaria o acumulada) | `GoogleMapsCompatible_Level6` | png, ~10 km, tasa instantánea |

   GRACE-FO: no se asume capa GIBS; se muestra como dato regional en el panel de evidencia desde `/plots/{id}/context`. Si la verificación encuentra una capa de anomalía TWS en GIBS, se agrega como P2.
4. **Fecha por capa ajustada a granularidad** con una función pura `snapToProduct(date, granularity, start)` testeada con vitest. Esto no es lógica del motor, es formato de request de tiles.
5. **Fallback de tiles**: listener `tileerror` cuenta errores; si superan un umbral o pasa un timeout (configurable, ejemplo 4 s) sin `load`, se reemplaza la capa por `L.imageOverlay` con la imagen estática del lote demo (`/static/layers/demo-casilda/<layer>_<date>.png` + bounds en JSON) generada por `demo-mode`. Alternativa descartada: service worker que cachee tiles (complejo, frágil en el primer load del jurado).
6. **Cliente de API tipado desde el JSON Schema exportado** por `domain-models` (`json-schema-to-typescript` en build). Alternativa descartada: tipos escritos a mano (se desincronizan con el motor).
7. **Estado local con React hooks + un hook `useEvaluation`** con debounce (ejemplo 300 ms) y `AbortController` + contador de request para descartar respuestas viejas. Alternativa descartada: Redux/Zustand (innecesario para una pantalla), React Query (útil, pero el caso es chico; se puede adoptar si el equipo ya lo domina).
8. **Indicador de cambio de ranking**: el front guarda el último `rank` por `rotation_id` y muestra la diferencia; esto es comparación de presentación, no recalcula puntaje. Animación FLIP con CSS transform; desactivada con `prefers-reduced-motion`.
9. **Procedencia**: componente `<PValueView>` que recibe un PValue de la API y renderiza valor formateado + `<ProvenanceBadge>` (texto corto + ícono + color) + tooltip accesible (`role="tooltip"`, `aria-describedby`, abre con foco, hover y tap). Los supuestos se resuelven contra `GET /assumptions` cacheado en memoria.
10. **Simulador de chat** como componente aislado que solo hace `POST /chat/simulate` con `{session_id, message, location?}` y renderiza el texto devuelto. El `session_id` es aleatorio por pestaña (está en el front, no en el motor).
11. **Tests**: vitest para funciones puras (snap de fecha, formato, diff de ranking); Playwright con `page.route` para mockear la API con fixtures JSON de `demo-mode` (tests deterministas) y un job aparte contra la API real en DEMO_MODE; `@axe-core/playwright` para accesibilidad; viewports 1920x1080, 1280x720 y 390x844.
12. **Configuración**: `VITE_API_BASE_URL` en build (Vercel env); `.env.example` sin secretos. GIBS no requiere credenciales.

## Risks / Trade-offs

- [Identificadores GIBS incorrectos o sin datos para la fecha] → verificar con GetCapabilities antes de codear (tarea 2.1); fallback estático.
- [SMAP/IMERG a baja resolución se ven como "pixeles gigantes" sobre el lote] → se explicita en la leyenda y se usa como argumento honesto de escala en el pitch.
- [CORS entre Vercel y la API en Render/Fly] → la API declara el origen de Vercel en CORS (change `api`); test de humo post-deploy.
- [Cold start de la API gratuita durante la demo] → checklist de pre-demo (change `demo-mode`) despierta la API minutos antes.
- [Tentación de "arreglar" números en el front] → regla explícita en spec y test que busca módulos de score en el front.
- [Tabla ilegible en celular] → vista de tarjetas por debajo de un breakpoint.

## Migration Plan

Deploy estático en Vercel desde `web/` (preview por PR, producción desde main). Rollback: promover el deploy anterior en Vercel. Plan B local: `npm run build && npm run preview` apuntando a la API local en DEMO_MODE.

## Open Questions

- Nombre visible de la app en el header ("Field Shift AR" es nombre de trabajo).
- Paleta y tipografía final (no cambia specs).
