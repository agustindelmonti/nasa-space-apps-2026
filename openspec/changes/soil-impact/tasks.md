# Tasks: soil-impact

## 1. Supuestos y entrada (P0)

- [ ] 1.1 Agregar entradas A-SOIL-01..11 a `assumptions.yaml` con valor de ejemplo, unidad, fuente o "pendiente AFA" y PENDING_AFA; verificar con el test de carga del registro que todos los ids parsean y validan formato
- [ ] 1.2 Definir el modelo de coeficientes de suelo resueltos dentro de `EngineInput` (cambio aditivo coordinado con domain-models) con validación de pesos (suma 1) y dominios; tests de "Pesos inválidos" y "Falta el aporte de carbono del centeno" en verde

## 2. Componentes (P0)

- [ ] 2.1 Implementar cobertura por unión de intervalos con arrastre cíclico entre campañas; tests "Soja continua con barbecho invernal" y "Superposición no se cuenta doble" en verde
- [ ] 2.2 Implementar carbono y nitrógeno con normalización clamp; tests "Gramínea aporta más que leguminosa" y "Vicia como leguminosa de servicio" en verde
- [ ] 2.3 Implementar malezas y raíces; tests "Soja continua en el mínimo", "Rotación diversa con invierno" y "Compactación informada" en verde

## 3. Agregación y salida (P0)

- [ ] 3.1 Implementar agregación ponderada, cotas y desglose por componente y campaña con procedencia DERIVED; tests "Índice dentro de cotas" y "Desglose suma al total" en verde
- [ ] 3.2 Test de invariancia a rotar el ciclo ("Rotación de campañas equivalente") con hypothesis sobre rotaciones válidas; `uv run pytest tests/engine/soil -q` en verde
- [ ] 3.3 Property test de monotonicidad al agregar servicio (escenario "Centeno sobre soja continua") y test documentado del caso N negativo; en verde

- [ ] 3.4 Implementar calendario mensual de suelo desnudo (sin cultivo vivo y sin cobertura) desde A-AGR-01 y A-SOIL-02; tests "Soja continua con invierno desnudo" y "Servicio cubre el invierno" en verde

## 4. NDVI como evidencia (P1)

- [ ] 4.1 Implementar cobertura observada desde el resumen NDVI resuelto, Evidencia y Faltante por discrepancia o ausencia; tests "Discrepancia entre modelo y satélite" y "Sin serie NDVI" en verde
- [ ] 4.2 Documentar en `docs/soil-index.md` la fórmula y la tabla de supuestos, y verificar con un test que cada id A-SOIL citado en el doc existe en `assumptions.yaml`
- [ ] 4.3 Adjuntar al calendario la fracción mensual observada de NDVI bajo A-SOIL-10 para la actual; tests "Evidencia NDVI de la actual" y "Sin resumen NDVI" en verde (P0 si el resumen NDVI está cacheado para la demo)
- [ ] 4.4 Aceptar pesos efectivos por prioridades con validación; test "Prioridad de carbono" en verde
