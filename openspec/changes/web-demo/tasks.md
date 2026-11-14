# Tasks: web-demo (P0 con partes P1/P2)

## 1. Scaffolding y cliente de API (P0)

- [ ] 1.1 Crear `web/` con Vite + React + TypeScript, ESLint y vitest; verificar `npm run build` y `npm test` en verde
- [ ] 1.2 Agregar Playwright con viewports 1920x1080, 1280x720 y 390x844 y un test de humo que carga la página; verificar `npx playwright test` en verde
- [ ] 1.3 Generar tipos TS desde el JSON Schema de `EngineInput`/`EngineOutput` (`schemas/`) y crear cliente `/api/v1` con errores tipados `{code, message, details}`; verificar con vitest contra un fixture de respuesta de `demo-mode`
- [ ] 1.4 Configurar `VITE_API_BASE_URL`, `.env.example` y chequeo de `GET /health` con indicadores "Modo demo" y "API caída"; verificar tests Playwright de los escenarios "API en modo demo" y "API caída"

## 2. Mapa y capas GIBS (P0)

- [ ] 2.1 Verificar contra GetCapabilities de GIBS (epsg3857/best) los identificadores, tileMatrixSet, formato, rango temporal y granularidad de NDVI MODIS, SMAP L4 rootzone, IMERG y capa base; volcar en `web/src/config/layers.json`; verificar con un script que pide un tile de cada capa sobre el lote demo y obtiene HTTP 200
- [ ] 2.2 Mapa Leaflet centrado en el lote con marcador o polígono, selector de capas y opacidad; verificar test Playwright "Capas disponibles" y "Pedido de tiles a GIBS" (intercepción de requests)
- [ ] 2.3 Selector de fecha con `snapToProduct` y validación de rango por capa; verificar vitest de ajuste de compuesto y Playwright "Fecha fuera de rango"
- [ ] 2.4 Leyenda por capa con unidad, dataset, resolución, limitación y enlace a glosario desde configuración; verificar Playwright "Limitación visible"

## 3. Ranking por actor (P0)

- [ ] 3.1 Tabla comparativa (rango, nombre, puntaje, desglose de tres términos, factibilidad con cuatro textos, ΔSuelo, riesgo) con fila actual rotulada; verificar Playwright "Ranking tal como llega de la API", "Rotación actual destacada", "Rotación no factible", "Factibilidad desconocida" y "Menos de 3 resultados"
- [ ] 3.2 Selector de actor desde `GET /actors/profiles` que dispara `POST /evaluate`; verificar Playwright "Propietario vs arrendatario"
- [ ] 3.3 Vista de tarjetas en celular para la tabla; verificar Playwright "Celular sin scroll horizontal"
- [ ] 3.4 Columnas de peor año, años con pérdida y lluvia sobre suelo desnudo; verificar Playwright "Años con pérdida visibles" y "Métrica en la tabla"

## 4. Evidencia y procedencia (P0)

- [ ] 4.1 Componentes de valor con procedencia, badge y tooltip accesible (hover, foco, tap) resolviendo supuestos con `GET /assumptions`; verificar Playwright "Supuesto marcado", "Tooltip de dato SMAP" y "Tooltip de supuesto"
- [ ] 4.2 Panel de rotación seleccionada con la tarjeta fija de 5 secciones y leyenda al pie; verificar Playwright "Tarjeta de 5 secciones" y "Faltantes visibles"
- [ ] 4.3 Leyendas fijas "Apoya, no reemplaza al agrónomo" y "Escenarios históricos, no predicción"; verificar Playwright "Leyendas siempre presentes"

- [ ] 4.4 Componente `<MonthStrip>` para el calendario de suelo desnudo con fila de NDVI observado; verificar Playwright "Calendario de la actual con NDVI" y "Comparar con una alternativa"
- [ ] 4.5 Timeline de vulnerabilidad por cultivo (helada y déficit) y barras de rango por clase; verificar Playwright "Déficit en enero", "Evento ausente" y "Barras de rango"

## 5. Simulador de chat (P0)

- [ ] 5.1 Componente de chat estilo mensajería contra `POST /chat/simulate` con botón "enviar ubicación del lote demo" y rótulo de simulación; verificar Playwright "Conversación de demo" y "Error del simulador"

## 6. Sliders y cambio de ranking (P1)

- [ ] 6.1 Sliders H, α, λ con rangos de la API, debounce y descarte de respuestas viejas; verificar Playwright "Cambio de λ" y "Respuestas fuera de orden"
- [ ] 6.2 Indicador de cambio de posición y animación FLIP con `prefers-reduced-motion`; verificar vitest del diff de ranking y Playwright "Subida de posición" y "Movimiento reducido"

- [ ] 6.3 Filtro por clase de año, sliders de prioridades de suelo y toggles de preferencias enviados a `/evaluate` (tabla según `display_order`), más filas de calor y lluvia extrema en el timeline cuando vengan en la respuesta; verificar Playwright "Solo años secos", "Preferencia de agua" y "Prioridad de carbono"
- [ ] 6.4 Lluvia sobre suelo desnudo en el calendario, tabla POWER vs IMERG en evidencia, robustez como texto y vista por tres miradas; verificar Playwright "Lluvia sobre el calendario", "Año con discrepancia" y "Robustez como conteo"

## 7. Glosario y fallback (P1)

- [ ] 7.1 Glosario desde `GET /glossary` con enlaces desde la UI; verificar Playwright "Término enlazado" y que existan los 8 términos mínimos
- [ ] 7.2 Fallback a imagen estática cacheada del lote demo con rótulo y fecha; verificar Playwright "GIBS caído en la demo" con requests a GIBS bloqueadas

## 8. Accesibilidad, deploy e integración (P1)

- [ ] 8.1 Integrar `@axe-core/playwright`, corregir violaciones y navegación por teclado; verificar "Chequeo axe" y "Sliders con teclado"
- [ ] 8.2 Test de guarda que falla si aparece lógica de score/VAN/riesgo en `web/src`; verificar que el test pasa y falla al introducir un módulo de prueba
- [ ] 8.3 Deploy en Vercel con `VITE_API_BASE_URL` de producción y CORS de la API; verificar carga de la URL pública y `GET /health` desde el navegador
- [ ] 8.4 Test E2E contra la API real en DEMO_MODE con red bloqueada salvo API y GIBS; verificar "Sin otras salidas de red"
- [ ] 8.5 Documentar en README de `web/` cómo correr, testear y desplegar, y las librerías OSS usadas; verificar que los comandos documentados corren tal cual

## 9. Pulido (P2)

- [ ] 9.1 Modo presentación (tipografía grande, ocultar controles secundarios) para 1280x720; verificar Playwright "Proyector" con capturas
- [ ] 9.2 Capa de anomalía GRACE-FO si GIBS la publica (según 2.1); verificar tile HTTP 200 y leyenda con limitación de ~300 km
- [ ] 9.3 Botón "Descargar ficha" contra `/rotation-sheet`; verificar Playwright "Descargar ficha"

## Sistema visual (P0)

- [ ] D.1 Cargar tokens de `DESIGN.md` como variables CSS y autoalojar Schibsted Grotesk, Atkinson Hyperlegible Next e IBM Plex Mono; íconos con lucide-react; verificar con un script que todo hex usado en `web/src` existe en el frontmatter
- [ ] D.2 Construir la franja de campañas como componente aislado con su leyenda y probarla con Playwright a 1920x1080 y 390x844
- [ ] D.4 Implementar los seis momentos de movimiento de DESIGN.md (reordenamiento FLIP, cifras, capas, entrada única, chat, carga) con prefers-reduced-motion; verificar con Playwright emulando reduced motion
- [ ] D.3 Correr `npx impeccable detect web/src` y resolver hallazgos primarios antes del domingo 13:00

## Agente (P1)

- [ ] A.1 Construir el panel "Preguntale a Rastrojo" con badges, sugerencias, indicador de modo y traza desplegable; test Playwright de traza y sugerencia
