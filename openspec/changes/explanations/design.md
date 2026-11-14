# Design: explanations

## Context

Ver proposal.md. El motor (`rotation-engine`) entrega un `EngineOutput` con resultados ordenados, desglose del puntaje, factibilidad, Evidencia, Beneficios, Faltantes y Riesgos, todos con procedencia (`domain-models`). Este módulo solo transforma esa salida en texto; no calcula nada nuevo. Lo consumen `api` (POST /evaluate, GET /glossary) y `whatsapp-channel` (resumen, detalle, glosario).

## Goals / Non-Goals

**Goals:** módulo puro y determinista; trazabilidad de cada número verificable por test; un único formateador numérico y un único parser compartidos por explicaciones y por las guardas del LLM de `whatsapp-channel`.

**Non-Goals:** redacción "creativa", personalización por usuario, internacionalización, renderizado HTML (lo hace `web-demo` a partir del estructurado o del texto con marcado mínimo).

## Decisions

1. **Ubicación: `fieldshift.application.explanations`**, funciones puras `explain(output, resolved_input, contrast=None, options) -> Explanation`. Vive en aplicación (no en engine) porque depende del catálogo de datasets y del glosario, que son datos; no hace I/O: recibe catálogo y glosario ya cargados. Alternativa descartada: generar texto dentro del motor (mezcla presentación con cálculo y ensucia el hash de salida).
2. **Plantillas como funciones Python con f-strings sobre valores ya formateados**, no Jinja2. Cada hueco numérico se llena con `cite(path)` que resuelve el valor en el documento citable, lo formatea y registra la cita `{token, path, provenance_kind, assumption_id?}`. Así es imposible escribir un número sin cita salvo que se tipee literal, y eso lo atrapa el test. Alternativa descartada: Jinja2 (dependencia extra, los números se cuelan como literales sin registro).
3. **Documento citable = `EngineOutput` + `EngineInput` resuelto con el mismo `input_hash`.** Rutas tipo JSON Pointer (`/results/2/score_breakdown/soil_term_usd_ha/value`). Se verifica que ambos hashes coincidan antes de generar. Alternativa descartada: citar solo la salida (obligaría al motor a re-emitir H, precios y fechas que ya están en la entrada).
4. **Formateador y parser argentinos propios** (`format_ar(value, unit)`, `parse_ar_numbers(text)`), con tabla de decimales por unidad en un único módulo, redondeo `Decimal.quantize(ROUND_HALF_UP)` sobre `repr` del float canónico. Alternativa descartada: `locale`/Babel (depende del locale del sistema operativo y rompe el determinismo entre máquinas).
5. **Test de trazabilidad**: extrae tokens numéricos con una regex que reconoce `-?\d{1,3}(\.\d{3})*(,\d+)?|\d+`, descarta tokens de la lista blanca (ids de supuesto, `(n/m)`, opciones de menú, nombres propios) y exige que cada token restante esté en el conjunto de tokens citados. Corre sobre todas las fixtures de `demo-mode` y sobre salidas generadas con hypothesis.
6. **Término dominante**: máximo por valor absoluto entre `npv_margin`, `soil_term` y `risk_term`; empate resuelto por ese orden fijo. Las frases asociadas son fijas por término.
7. **Propietario vs arrendatario**: la capa de aplicación corre el motor dos veces (OWNER y TENANT) con la misma entrada salvo el perfil; el generador recibe ambas salidas y valida que lote, rotaciones y escenarios coincidan. El cambio de posición se atribuye al término cuyo valor cambió más en valor absoluto entre perfiles (ambos valores existen en las salidas; no se cita la diferencia).
8. **Partición WhatsApp**: algoritmo voraz determinista: acumular párrafos mientras quepan (reservando el largo del marcador `(n/m)` calculado con m estimado y recalculado hasta punto fijo); si un párrafo no entra, cortar por línea y luego por palabra. Nunca se corta dentro de un token de cita (los tokens se protegen como unidades indivisibles). Las leyendas y la nota de supuestos se fuerzan en el último mensaje.
9. **Glosario como YAML versionado** (`data/glossary.yaml`), con huecos `{dataset:SMAP_L4.spatial_resolution}` que se resuelven contra el catálogo de datasets de `nasa-ingestion`. Alternativa descartada: glosario hardcodeado en código (los agrónomos de AFA no pueden revisarlo).
10. **Versión de plantillas** (`templates_version`, semver manual) en la salida estructurada; los snapshot tests fallan si cambia el texto sin bump.
11. **Incertidumbre**: plantilla fija "en años secos el margen fue de X a Y; en años húmedos, de Z a W" citando el rango de margen por clase del resultado, y lo mismo con el agua a la siembra del rango hídrico de water-feasibility. El Riesgo se explica como "en el peor q de los años históricos ganaste en promedio tanto menos que en un año medio" (expected shortfall de márgenes, A-ACT-05); nunca como "el margen de los años DRY". Alternativa descartada: mostrar solo el esperado con un desvío estándar (no se entiende y esconde la cola).
12. **Calendarios**: suelo desnudo mes a mes con frases por tramo ("de junio a septiembre el lote queda sin cultivo vivo") y la fracción observada de NDVI bajo umbral como evidencia OBSERVED de la actual; vulnerabilidad como lista de meses con nivel MEDIUM o HIGH por cultivo y evento. Sin cálculos: todos los números vienen del resultado.

## Risks / Trade-offs

- [Textos rígidos y repetitivos] → aceptado: la prioridad es la trazabilidad; la capa LLM opcional de `whatsapp-channel` puede reformular con guardas.
- [El motor no expone algún número que el texto quiere citar] → el texto usa comparación cualitativa y se pide a `rotation-engine` que lo agregue. La diferencia contra la actual ya sale de `score_delta_vs_current`; los rangos por clase salen del motor (margen) y de water-feasibility (balance hídrico).
- [Falsos positivos del extractor con nombres que contienen dígitos] → lista blanca cerrada y revisada en code review.
- [Límite de 1600 caracteres cambia según proveedor] → límite configurable; default documentado como dato de plataforma, no agronómico.

## Open Questions

- Lista exacta de expresiones prohibidas y frases fijas: la redacta el equipo con revisión de un agrónomo de AFA si está disponible (no cambia la estructura).
- Cuántas rotaciones mostrar en el resumen WhatsApp (por defecto top 3 más la actual), configurable.
