# Tasks: rotation-engine

## 1. Entrada y candidatas (P0)

- [ ] 1.1 Definir el catálogo de 5 rotaciones como datos (ids estables) y la forma canónica cíclica; tests "Actual igual a una del catálogo" y "Actual definida por el usuario" en verde
- [ ] 1.2 Agregar a EngineInput/resultado (aditivo, coordinado con domain-models) supuestos resueltos, estado hídrico, `eligible`, `exclusion_reasons`, `water_adjustments`; verificar regenerando JSON Schema sin errores

## 2. Evaluación (P0)

- [ ] 2.1 Implementar traducción de estado hídrico a ajustes y factibilidad de rotación; tests "Soja de segunda infactible en años secos", "Servicio nunca factible", "Estado hídrico ausente" y "Rotación sin ajustes" en verde
- [ ] 2.2 Implementar Riesgo (ES con escenario de borde fraccionado y AF); tests "Cola de un tercio exacta", "Escenario de borde fraccionado" y "Sin variabilidad" en verde
- [ ] 2.3 Implementar puntaje y desglose; test "Desglose del puntaje" en verde

## 3. Filtrado y ranking (P0)

- [ ] 3.1 Implementar restricciones con todos los motivos y captura de faltantes por rotación; tests "Actor sin doble cultivo", "Dos motivos a la vez" y "Falta precio de trigo" en verde
- [ ] 3.2 Implementar ranking con clave total y rango 1..N; tests "Empate en puntaje" y "Orden de entrada irrelevante" en verde
- [ ] 3.3 Implementar garantía de al menos 3 opciones y advertencia LOW_ELIGIBLE_COUNT; test "Restricciones muy duras" en verde

## 4. Empaquetado (P0)

- [ ] 4.1 Implementar `evaluate` end-to-end con `input_hash` y `ENGINE_VERSION`; tests "Mismo input, mismos bytes" y "Ejecución sin red" (con sockets bloqueados vía fixture) en verde con el lote demo
- [ ] 4.2 Documentar la tubería y las fórmulas en `docs/engine.md`; verificar que los ejemplos numéricos del doc coinciden con los tests (`uv run pytest tests/engine -q` en verde)
