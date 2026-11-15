# Design: rotation-search

## Contexto

`rastrojo.engine.rotation.evaluate` ya recibe cualquier lista de candidatas (`EngineInput.candidates`) y la deduplica por equivalencia cíclica (`canonical_key`). Evaluar una rotación en las 41 campañas tarda unos 0,1 s, así que unas 300 candidatas por actor y filtro llevan del orden de 30 s: viable como precálculo, no por pedido (la función de Vercel corta a 60 s).

## Decisiones

1. **Campañas válidas.** Producto de invierno ∈ {ninguno, trigo, vicia, centeno, avena} y verano ∈ {ninguno, soja de primera, soja de segunda, maíz temprano, maíz tardío}, filtrado por las reglas del dominio (`Campaign._rules`) y por las de poda:
   - A-AGR-02: soja de segunda y maíz tardío (doble cultivo de verano) solo después de trigo, nunca después de un servicio.
   - A-AGR-03: un servicio de invierno solo antes de un cultivo de verano de primera (soja de primera o maíz temprano); no hay campaña de solo servicio ni de trigo sin verano.
   Resultado esperado: 10 campañas.
2. **Rotaciones.** Secuencias de 1 a 3 campañas (A-AGR-04 fija el largo máximo), en forma canónica: se descartan las periódicas (AA, AAA, ABAB no existe con largo ≤ 3) y las rotaciones de un mismo ciclo (ABC = BCA = CAB) quedan una sola vez, con el representante lexicográfico mínimo de `canonical_key`.
3. **Reglas de ciclo (A-AGR-05).** Cada ciclo incluye al menos una gramínea (maíz, trigo, centeno o avena) y ningún cultivo de verano de la misma especie más de dos campañas seguidas, contando el ciclo como circular. Estas reglas son agronómicas, no económicas: el puntaje decide entre las que quedan.
4. **Siempre incluidas.** El catálogo y la rotación actual se evalúan aunque no pasen las reglas, para que la comparación con lo que ya se muestra sea directa.
5. **Ids y nombres.** Id `G_` + 8 hex del SHA-256 de la clave canónica (estable entre corridas). Nombre generado desde las campañas, por ejemplo "Trigo / Soja 2ª → Maíz". Si la candidata coincide con una del catálogo, conserva id y nombre del catálogo.
6. **Búsqueda.** Una sola llamada a `evaluate` con todas las candidatas (el motor ya ordena, filtra por restricciones y deduplica). Del resultado se guardan:
   - el ranking de elegibles con puntaje, margen anual esperado, ΔSuelo, riesgo, estado hídrico y si es del catálogo;
   - el frente de Pareto: elegibles no dominadas en (margen esperado ↑, ΔSuelo ↑, riesgo ↓), con desempate por id;
   - la mejor del catálogo y la diferencia de puntaje de la mejor encontrada contra ella;
   - conteos: campañas válidas, rotaciones generadas, podadas por regla, evaluadas, elegibles.
7. **Precálculo.** `scripts/precompute_search.py` corre la búsqueda para OWNER, TENANT, COOP y BANK con los filtros ALL, DRY, NORMAL y WET, y escribe `data/fixtures/demo/search/<actor>_<filtro>.json` con `input_hash` (del `EngineInput` de la búsqueda), `engine_version` y `generator_version`. La tarea diaria lo regenera después del snapshot de clima.
8. **API.** `GET /api/v1/rotations/search` lee el fixture. Si falta, responde 404 con un código tipado (`SEARCH_NOT_PRECOMPUTED`), no evalúa.
9. **Web.** Debajo del ranking, una sección compacta con las 5 mejores encontradas para el actor y filtro elegidos, marcando cuáles superan a la mejor del catálogo y cuáles están en el frente de Pareto, y una nota: "con el perfil predefinido; los sliders y el arriendo no aplican a la búsqueda".

## Alternativas descartadas

- **Búsqueda heurística u optimizador.** Innecesaria con unas cientos de candidatas: la exhaustiva da la óptima garantizada dentro de las reglas y es más fácil de explicar.
- **Evaluar en cada pedido.** Excede el tiempo de la función serverless y repite trabajo idéntico; el motor es determinista, así que precalcular es equivalente.
- **Rotaciones de 4 o más campañas.** Multiplica el espacio por 10 y casi no aparece en la práctica de la zona núcleo; queda como parámetro (A-AGR-04).

## Riesgos

- Las reglas de poda pueden excluir algo que un agrónomo consideraría razonable. Mitigación: son supuestos con id, la salida informa cuántas se podaron por cada regla y AFA las puede revisar.
- Con supuestos económicos de ejemplo, "la mejor" depende de esos valores. La web y el pitch lo dicen.
