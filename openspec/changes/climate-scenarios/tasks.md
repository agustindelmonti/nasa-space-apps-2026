# Tasks: climate-scenarios

## 1. Modelos y configuración (P0)

- [ ] 1.1 Definir modelos frozen `WindowDef`, `ClassificationConfig`, `Exclusion`, `TieBreak`, `ClassificationResult` en `fieldshift.engine.climate`; verificar con test que rechaza campos extra y ventanas con inicio posterior al fin
- [ ] 1.2 Cargar A-CLI-01 a A-CLI-04 en `assumptions.yaml` con estado PENDING_AFA y resolverlos en la aplicación hacia `ClassificationConfig`; verificar con test "Ventana cambiada por agrónomos"

## 2. Acumulado y completitud (P0)

- [ ] 2.1 Implementar el acumulado por ventana con `math.fsum`, días esperados por calendario (bisiestos incluidos) y conteo de faltantes; verificar con tests "Verano que cruza el año calendario" y "Año bisiesto"
- [ ] 2.2 Implementar exclusiones `MISSING_DAYS` e `INCOMPLETE_WINDOW` y el chequeo de fuente única `MIXED_SOURCES`; verificar con tests "Año con huecos excluido", "Campaña en curso excluida" y "Fuentes mezcladas rechazadas"

## 3. Clasificación (P0)

- [ ] 3.1 Implementar terciles por rango con redondeo a 0.1 mm, desempate por año, resto a NORMAL y límites DERIVED; verificar con tests "N divisible por 3", "Resto asignado a NORMAL", "Empate en el límite de tercil" y "Ruido de punto flotante"
- [ ] 3.2 Implementar mínimo de años `INSUFFICIENT_YEARS` y pesos 1/N con frecuencia por clase; verificar con tests "Pocos años" y "Pesos de 31 años"
- [ ] 3.3 Agregar test de propiedad (hypothesis) de permutación de la serie y snapshot de la salida canónica del lote de demo; verificar con `uv run pytest tests/engine/climate -q` en verde y con red bloqueada

## 4. Cruce IMERG e integración (P1)

- [ ] 4.1 Implementar cruce POWER vs IMERG que solo agrega advertencias según A-CLI-04; verificar con tests "Discrepancia advertida" y "Sin IMERG"
- [ ] 4.2 Integrar en la aplicación: desde la caché del lote de demo construir los escenarios de invierno y verano para `EngineInput`; verificar con test de integración en `DEMO_MODE=1` que los pesos suman 1 y la salida cita la fuente
