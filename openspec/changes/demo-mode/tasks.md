# Tasks: demo-mode (P0 con partes P1/P2)

## 1. Lote demo y configuración (P0)

- [ ] 1.1 Registrar `A-DEMO-01` (ubicación y superficie placeholder de `demo-casilda`) en `assumptions.yaml` y definir el Lote demo; verificar test "Lote demo válido" y "Lote demo marcado como supuesto"
- [ ] 1.2 Agregar `DEMO_MODE` a `Settings` con credenciales opcionales en modo demo; verificar test que instancia `Settings` sin credenciales con `DEMO_MODE=1` y falla sin él

## 2. Fixtures NASA (P0)

- [ ] 2.1 Descargar con los clientes de `nasa-ingestion` POWER, SMAP L4, IMERG, GRACE-FO y MODIS NDVI para `demo-casilda` y copiarlos a `data/fixtures/demo/`; verificar test "Fixtures completos"
- [ ] 2.2 Generar `manifest.json` con dataset, colección, variable, período, resolución, fecha de descarga, origen y SHA-256, y comando de verificación; verificar tests "Checksum alterado" y "Período suficiente"
- [ ] 2.3 Implementar fuente de datos desde fixtures y su inyección con `DEMO_MODE=1`; verificar tests "Arranque sin red" (sockets bloqueados) y "Coordenadas sin fixtures"
- [ ] 2.4 Exponer modo demo y versión de fixtures en `GET /health` (coordinar con `api`); verificar test "Health informa el modo"

## 3. Económicos de ejemplo (P0)

- [ ] 3.1 Crear `economics.example.yaml` con cada parámetro como A-DEMO-02 a A-DEMO-06 con fuente y fecha (valores y fuentes provistos por el responsable de `economics`) y registrar los ids en `assumptions.yaml`; verificar tests "Parámetro sin fuente rechazado" y "Rótulo de ejemplo visible"

## 4. Snapshot del motor (P0)

- [ ] 4.1 Generar snapshots canónicos de `demo-casilda` para OWNER, TENANT, COOP y BANK y el test de comparación byte a byte; verificar tests "Salida estable" y "Cambio detectado"
- [ ] 4.2 Reporte de diferencia de orden entre OWNER y TENANT; verificar test "Rankings distintos por actor"

## 5. Guion y plan B (P0)

- [ ] 5.1 Escribir `docs/demo/script.md` con los 7 bloques, tiempos, qué se muestra, qué se dice y quién; verificar test que parsea la tabla ("Tiempos cerrados") y revisión de "Cierre honesto"
- [ ] 5.2 Escribir `docs/demo/plan-b.md` con disparadores, comandos exactos de ejecución local en DEMO_MODE y umbral para pasar al video; verificar corriendo los comandos tal cual en una máquina limpia sin red
- [ ] 5.3 Ensayar la demo dos veces con cronómetro y ajustar tiempos; verificar registro de duración <= 4:00 en el guion

## 6. Regeneración y capas estáticas (P1)

- [ ] 6.1 Script de regeneración en un comando con validación, reemplazo atómico y reporte de diff; verificar tests "Sin credenciales" y "Diff reportado" con fuentes mockeadas
- [ ] 6.2 Descarga de imágenes GIBS del entorno del lote (NDVI, SMAP L4, IMERG, base) con JSON de capa, fecha y bounds, publicadas como estáticos del front; verificar test "Imagen con metadatos"

## 7. Checklist de pre-demo (P1)

- [ ] 7.1 Comando `predemo` con ítems, timeouts, críticos y código de salida; verificar tests "API desplegada caída", "Todo en orden" y "Sin red en la sede" con servicios mockeados
- [ ] 7.2 Correr `predemo` contra los deploys reales el sábado antes de las 18:30; verificar salida todo OK pegada en el issue o canal del equipo

## 8. Video y material (P1/P2)

- [ ] 8.1 (P1) Grabar el video de respaldo del flujo completo en local con DEMO_MODE y guardarlo offline; verificar ítem de video en `predemo`
- [ ] 8.2 (P2) Escribir `docs/demo/video.md` con guion, tomas, textos en pantalla, créditos NASA y de librerías y declaración de IA; verificar revisión con el escenario "Créditos completos"
