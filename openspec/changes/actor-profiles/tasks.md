# Tasks: actor-profiles

## 1. Perfiles predefinidos (P0)

- [ ] 1.1 Agregar A-ACT-01..06 a `assumptions.yaml` con valores de ejemplo, fuente y PENDING_AFA; verificar con el test de carga del registro y el test "q fuera de rango"
- [ ] 1.2 Implementar construcción de los cuatro perfiles desde el registro con procedencia ASSUMPTION; tests "Listado de perfiles" y "Horizontes contrastantes" en verde
- [ ] 1.3 Implementar el Faltante de arrendamiento para TENANT; test "TENANT sin alquiler cargado" en verde

## 2. Demo con rankings distintos (P0)

- [ ] 2.1 Escribir el test de rankings distintos sobre el fixture demo-casilda (escenario "OWNER y TENANT difieren"); `uv run pytest tests/demo/test_actor_rankings.py -q` en verde sin red

## 3. Perfil personalizado (P1)

- [ ] 3.1 Implementar `custom_profile` con validación de sliders y procedencia por campo; tests "Slider fuera de rango" y "Personalizado desde TENANT" en verde

## 4. Sensibilidad (P1)

- [ ] 4.1 Implementar grilla y recombinación reutilizando el ranking del motor; tests "Grilla sobre λ", "Grilla inválida" y "Repetición idéntica" en verde
- [ ] 4.2 Implementar quiebres analíticos para α y λ; test "Quiebre analítico" y property test con hypothesis que verifica que el ranking cambia entre los puntos de grilla que encierran cada quiebre; en verde
- [ ] 4.3 Implementar el caso de uso de aplicación y documentar el contrato propuesto para `api` en `docs/sensitivity.md`; verificar con un test del caso de uso sobre el fixture demo
