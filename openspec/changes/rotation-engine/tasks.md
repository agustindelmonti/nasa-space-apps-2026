# Tasks: rotation-engine

## 1. Entrada y candidatas (P0)

- [ ] 1.1 Definir el catálogo de 5 rotaciones como datos (ids estables) y la forma canónica cíclica; tests "Actual igual a una del catálogo" y "Actual definida por el usuario" en verde
- [ ] 1.2 Consumir los agregados acordados en domain-models (supuestos resueltos, insumos hídricos, `eligible`, `exclusion_reasons`, `water_adjustments`, `score_delta_vs_current`, rango de margen, calendarios); verificar regenerando JSON Schema sin errores

## 2. Evaluación (P0)

- [ ] 2.1 Invocar water-feasibility como submódulo, traducir su estado por escenario a ajustes y armar la factibilidad informada; tests "Soja de segunda infactible en años secos", "Servicio nunca factible", "Estado hídrico desconocido en un escenario", "Rotación sin ajustes", "Factibilidad desconocida no descarta" y "Una sola definición de umbrales" en verde
- [ ] 2.2 Implementar Riesgo (ES con escenario de borde fraccionado y AF); tests "Cola de un tercio exacta", "Escenario de borde fraccionado" y "Sin variabilidad" en verde
- [ ] 2.3 Implementar puntaje exacto VAN + α·ΔSuelo − λ·Riesgo y desglose de tres términos; test "Desglose del puntaje" en verde

## 3. Filtrado y ranking (P0)

- [ ] 3.1 Implementar restricciones con todos los motivos y captura de faltantes por rotación; tests "Actor sin doble cultivo", "Capital sin tope", "Dos motivos a la vez" y "Falta precio de trigo" en verde
- [ ] 3.2 Implementar ranking con clave total y rango 1..N; tests "Empate en puntaje" y "Orden de entrada irrelevante" en verde
- [ ] 3.3 Implementar garantía de al menos 3 opciones y advertencia LOW_ELIGIBLE_COUNT; test "Restricciones muy duras" en verde

- [ ] 3.4 Implementar `score_delta_vs_current`, rango de margen por clase y copia de calendarios; tests "Diferencia calculada por el motor", "Actual sin puntaje", "Rango con tres clases", "Puntaje intacto" y "Calendarios presentes" en verde
- [ ] 3.5 Copiar años con pérdida y margen del peor año (economics) y lluvia sobre suelo desnudo (soil-impact) al resultado; tests "Conteo de años con pérdida", "Puntaje intacto por métricas de pérdida" y "Métrica presente para todas" en verde (P0)

## 4. Empaquetado (P0)

- [ ] 4.1 Implementar `evaluate` end-to-end con `input_hash` y `ENGINE_VERSION`; tests "Mismo input, mismos bytes" y "Ejecución sin red" (con sockets bloqueados vía fixture) en verde con el lote demo
- [ ] 4.2 Documentar la tubería y las fórmulas en `docs/engine.md`; verificar que los ejemplos numéricos del doc coinciden con los tests (`uv run pytest tests/engine -q` en verde)

## 5. Restricciones y filtros adicionales (P1)

- [ ] 5.1 Implementar filtro por clase de año (ALL, DRY, NORMAL, WET) con re-ponderación, control de A-CLI-03 sobre el conjunto completo y advertencia; tests "Solo años secos", "Sin filtro" y "Filtro sin escenarios" en verde
- [ ] 5.2 Implementar MACHINERY_WINDOW_CONFLICT desde ventanas del perfil y A-AGR-01; test "Siembra fuera de la ventana de maquinaria" en verde
- [ ] 5.3 Pasar a soil-impact los pesos efectivos de actor-profiles; tests "Prioridades solo cambian ΔSuelo" y de actor-profiles "Prioridades nulas no cambian nada" en verde
