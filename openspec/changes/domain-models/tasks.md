# Tasks: domain-models (P0)

## 1. Scaffolding (P0)

- [x] 1.1 Crear proyecto `uv` (Python 3.12) con layout `src/rastrojo/{domain,engine,data,application,adapters}` y verificar `uv run python -c "import rastrojo"`
- [x] 1.2 Agregar pydantic, pydantic-settings, pytest, hypothesis, ruff, mypy; verificar `uv run pytest` en verde con 0 tests

## 2. Núcleo de procedencia (P0)

- [x] 2.1 Implementar `DomainModel`, `Source`, `Assumption`, `Provenance` (unión discriminada) y `PValue`; tests de los escenarios "Valor con procedencia" y "Fuente de datos descriptiva" en verde
- [x] 2.2 Implementar JSON canónico y `input_hash`; tests de hash reproducible, NaN rechazado e ida y vuelta estable en verde

## 3. Entidades (P0)

- [x] 3.1 Implementar Lote y Suelo con validadores de rango y bbox; tests de escenarios Lote y Suelo en verde
- [x] 3.2 Implementar catálogo de cultivos y Rotación con reglas de campaña; tests de soja de segunda sin antecesor y rotación válida en verde
- [x] 3.3 Implementar PerfilActor, ParámetrosEconómicos y EscenarioClimático; tests de H inválido, precio sin fecha y pesos en verde
- [x] 3.4 Implementar resultado de evaluación, Evidencia, Faltante, Riesgo, `EngineInput` y `EngineOutput`; test de desglose consistente en verde
- [x] 3.5 Exportar JSON Schema de `EngineInput`/`EngineOutput` a `schemas/` y verificar con un script que regenera sin diff

## 4. Agregados de la reconciliación (P0)

- [x] 4.1 Ampliar `Source.dataset` con FIELD_HAMMER, SRTM, ECOSTRESS y GLDAS, validar áreas de supuesto (incluida DEMO) y la regla OBSERVED con `is_modeled=true` para productos externos; tests "Dato de SoilGrids marcado como modelado", "Dataset nuevo admitido", "Área de supuesto desconocida" y "Humedad SMAP L4 tal cual se publica" en verde
- [x] 4.2 Agregar a `EngineInput` supuestos resueltos, insumos hídricos por escenario, SMAP inicial, TWS, resumen NDVI y filtro por clase de año; tests "Estado hídrico precalculado rechazado", "Insumo opcional ausente" y "Supuestos resueltos en la entrada" en verde
- [x] 4.3 Canonicalizar `input_hash` ordenando candidatas por id y escenarios por año; test "Orden de listas irrelevante para el hash" en verde
- [x] 4.4 Agregar clases anual, de invierno y de verano a EscenarioClimático y A-AGR-01 al catálogo; tests "Clases por estación y anual" y "Calendario desde un único supuesto" en verde
- [x] 4.5 Ampliar el resultado por rotación (elegibilidad, motivos, ajustes hídricos, `score_delta_vs_current`, rango de margen por clase, calendarios mensuales, años con pérdida, margen del peor año, lluvia sobre suelo desnudo, factibilidad UNKNOWN y filtro con NORMAL; sin términos de prioridad en el desglose); tests "Diferencia contra la actual", "Rango de margen por clase", "Factibilidad desconocida admitida" y "Calendarios de 12 meses" en verde

## 5. Agregados de perfil y economía (P1)

- [x] 5.1 PerfilActor con capital opcional, pesos de prioridad de suelo (EROSION_COVER, OM_CARBON, NITROGEN, WEED_CONTROL, ROOTS) y ventanas de maquinaria; tests "Sin tope de capital", "Peso de prioridad fuera de rango", "Prioridad de presentación en el perfil" y "Mes de maquinaria inválido" en verde
- [x] 5.2 ParámetrosEconómicos con base de precio, modo de cosecha, flete por t y arrendamiento opcional; tests "Precio sin base" y "Arrendamiento con dos unidades" en verde
