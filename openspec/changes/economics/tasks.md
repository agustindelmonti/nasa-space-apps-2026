# Tasks: economics

## 1. Parámetros (P0)

- [ ] 1.1 Extender ParámetrosEconómicos (aditivo, coordinado con domain-models) con base de precio, modo de cosecha, comercialización, flete por t y arrendamiento opcional; tests de validación (retención >= 1 rechazada, base obligatoria) en verde
- [ ] 1.2 Agregar A-ECO-01..04 a `assumptions.yaml`; verificar con el test de carga del registro

## 2. Margen (P0)

- [ ] 2.1 Implementar margen por cultivo y escenario con clase por estación; tests "Margen de soja de primera en año normal" y "Clase de año por estación" en verde
- [ ] 2.2 Implementar servicio como costo y base de precio; tests "Centeno sin precio" y "Precio disponible no se retiene dos veces" en verde
- [ ] 2.3 Implementar ajuste hídrico NOT_SOWN/FORCE_DRY; test "Soja de segunda no sembrada" en verde
- [ ] 2.4 Implementar margen de campaña y arrendamiento; tests "Arrendamiento en quintales" y "Sin arrendamiento" en verde
- [ ] 2.5 Implementar recolección de faltantes y error tipado; tests "Falta el rinde DRY de trigo" y "Cero explícito" en verde

## 3. Agregados (P0)

- [ ] 3.1 Implementar margen esperado, matriz (posición, año) y VAN en forma cerrada; tests "Pesos uniformes", "Matriz completa", "Ciclo parcial con H=1", "Tasa cero" en verde
- [ ] 3.2 Property test con hypothesis: forma cerrada AF·Ē igual a la suma explícita por fases (tolerancia 1e-9) e invariancia al rotar campañas; en verde

## 4. Capital de trabajo y fechas (P1)

- [ ] 4.1 Implementar calendario mensual, ingresos con desfase y pico; tests "Pico antes de la cosecha" y "Arrendamiento adelantado" en verde
- [ ] 4.2 Implementar advertencia de fechas mezcladas; test "Fechas mezcladas" en verde y `uv run pytest tests/engine/economics -q` en verde
