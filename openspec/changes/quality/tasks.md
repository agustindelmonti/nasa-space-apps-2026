# Tasks: quality

## 1. Herramientas y CI mínimo (P0)

- [ ] 1.1 Configurar ruff, mypy, pytest, pytest-cov, hypothesis y syrupy en `pyproject.toml` con marcadores `network` y `slow`; verificar `uv run ruff check . && uv run pytest -q` en verde
- [ ] 1.2 Crear `.github/workflows/ci.yml` con jobs lint, types y test sin secretos; verificar que el workflow corre en un push de prueba y queda visible en el commit

## 2. Pureza y determinismo (P0)

- [ ] 2.1 Implementar el test AST de imports con listas de prohibidos y permitidos y detección de `now/today/utcnow`; verificar que falla con un archivo temporal que importa `random` (escenario "Import prohibido") y pasa con engine limpio
- [ ] 2.2 Implementar determinismo en el mismo proceso para los cuatro perfiles con diff de primera ruta; test "Dos corridas iguales" en verde
- [ ] 2.3 Implementar `fieldshift.tools.cli_eval` y el test entre procesos con `PYTHONHASHSEED` distintos; test "Semillas de hash distintas" en verde

## 3. Propiedades (P1)

- [ ] 3.1 Escribir estrategias `engine_inputs()` con `derandomize=True`, insumos hídricos sintéticos y prioridades opcionales; verificar que generan entradas válidas (100 ejemplos sin errores de validación)
- [ ] 3.2 Property tests de λ y α (escenarios "Más λ no favorece a la más riesgosa" y "Más α no penaliza a la que más mejora el suelo") en verde
- [ ] 3.3 Property tests de permutación (con `input_hash` invariante) y escala monetaria (escenarios "Candidatas reordenadas" y "Precios por k") en verde
- [ ] 3.4 Property tests con prioridades del productor (escenarios "Prioridades aleatorias" y "Prioridades en cero") en verde

## 4. Snapshots, cobertura y tipos (P1)

- [ ] 4.1 Generar snapshots del lote demo por perfil y el lock de versión con hashes; test "Cambio de fórmula sin bump" verificado con un cambio de prueba que luego se revierte
- [ ] 4.2 Activar `--cov-fail-under=90` para engine + domain y el paso de cobertura solo engine; verificar que el job falla si se excluye un módulo de tests (escenario "Cobertura insuficiente")
- [ ] 4.3 Activar mypy `--strict` sobre engine y domain y corregir hasta 0 errores; verificar con `uv run mypy --strict src/fieldshift/engine src/fieldshift/domain`

## 5. Endurecimiento (P2)

- [ ] 5.1 Agregar caché de uv y fijar versiones de acciones en el workflow; verificar que el tiempo total del CI baja y sigue en verde
