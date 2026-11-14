# Tasks: domain-models (P0)

## 1. Scaffolding (P0)

- [ ] 1.1 Crear proyecto `uv` (Python 3.12) con layout `src/fieldshift/{domain,engine,data,application,adapters}` y verificar `uv run python -c "import fieldshift"`
- [ ] 1.2 Agregar pydantic, pydantic-settings, pytest, hypothesis, ruff, mypy; verificar `uv run pytest` en verde con 0 tests

## 2. Núcleo de procedencia (P0)

- [ ] 2.1 Implementar `DomainModel`, `Source`, `Assumption`, `Provenance` (unión discriminada) y `PValue`; tests de los escenarios "Valor con procedencia" y "Fuente de datos descriptiva" en verde
- [ ] 2.2 Implementar JSON canónico y `input_hash`; tests de hash reproducible, NaN rechazado e ida y vuelta estable en verde

## 3. Entidades (P0)

- [ ] 3.1 Implementar Lote y Suelo con validadores de rango y bbox; tests de escenarios Lote y Suelo en verde
- [ ] 3.2 Implementar catálogo de cultivos y Rotación con reglas de campaña; tests de soja de segunda sin antecesor y rotación válida en verde
- [ ] 3.3 Implementar PerfilActor, ParámetrosEconómicos y EscenarioClimático; tests de H inválido, precio sin fecha y pesos en verde
- [ ] 3.4 Implementar resultado de evaluación, Evidencia, Faltante, Riesgo, `EngineInput` y `EngineOutput`; test de desglose consistente en verde
- [ ] 3.5 Exportar JSON Schema de `EngineInput`/`EngineOutput` a `schemas/` y verificar con un script que regenera sin diff
