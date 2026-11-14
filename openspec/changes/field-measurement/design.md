# Design: field-measurement

## Context

Ver proposal.md. Capability P2: se construye solo si el MVP está verde. Usa `domain-models` (Source, PValue), la caché SMAP L4 de `nasa-ingestion` y el adaptador FastAPI de `api`. No toca el motor.

Principio físico: el impactómetro Clegg deja caer una masa con acelerómetro desde una altura fija y lee la desaceleración pico; suelo más duro, pico mayor y pulso más corto. Acá la masa es un carro de ~2 kg que corre sobre un riel o tubo guía con el celular fijado, y el sensor es el acelerómetro del teléfono (parámetros del master doc, A-FLD-02).

## Goals / Non-Goals

**Goals:** captura simple desde el navegador del celular; resultados relativos honestos; una tarjeta que explique campo vs satélite en el pitch.

**Non-Goals:** app nativa, calibración, procesamiento de la señal cruda en el servidor, persistencia en base de datos.

## Decisions

1. **Picos calculados en el cliente.** La web lee DeviceMotion (`accelerationIncludingGravity`), detecta cada impacto (umbral sobre la magnitud) y envía por golpe el pico y la duración del pulso, más la frecuencia de muestreo efectiva medida. Alternativa descartada: enviar la señal cruda (más volumen y más trabajo de backend sin mejorar la honestidad del resultado).
2. **Mediana y coeficiente de variación** por punto; robustos a un golpe raro. Alternativa descartada: media (sensible a golpes mal dados).
3. **Normalización dentro de sesión y dispositivo**, índice = 100 × mediana punto / mediana de medianas, categoría por terciles de posición (misma regla de desempate que `climate-scenarios`: por id). Alternativa descartada: escala absoluta tipo "Clegg Impact Value" (exige calibración que no tenemos).
4. **Saturación declarada**: muchos celulares tienen rango de ±8 g o ±16 g y un Clegg real registra decenas a cientos de g. Por eso se registra también la duración del pulso (menos sensible a saturación) y se marcan golpes saturados. Se documenta como limitación principal.
5. **Almacenamiento**: `data/field/<plot_id>/<session_id>.json` con el JSON canónico de la sesión; idempotencia comparando el hash del contenido. Alternativa descartada: SQLite (innecesario para P2).
6. **SMAP para la tarjeta**: se usa la media diaria de `sm_rootzone` de la caché; si la fecha no está, la más cercana anterior dentro de A-FLD-06. En la demo offline, la sesión de ejemplo y SMAP vienen de `data/fixtures/demo/`.
7. **Rutas**: `POST /api/v1/plots/{id}/field-readings` y `GET /api/v1/plots/{id}/field-readings`, ya listadas en `api` como P2 con los códigos SESSION_CONFLICT y SAMPLING_RATE_TOO_LOW en su catálogo.
8. **`FIELD_HAMMER` en Source**, ya agregado al enum de datasets de `domain-models`.
9. **Accesorio v0 (A-FLD-02)**: carro de ~2 kg sobre riel o tubo, topes a 150, 300 y 450 mm. v0 usa solo 150 mm porque con alturas mayores el acelerómetro del celular (típicamente ±8 g o ±16 g) satura en suelo firme; las otras alturas quedan para v1. Corrige el valor previo de 30 cm. La sesión declara masa en kg y altura en mm. Alternativa descartada: altura libre declarada por sesión (rompe la comparación dentro de la sesión).
10. **v1 futura (fuera de alcance)**: ESP32 con ADXL375 (±200 g, sin saturación en este rango) calibrada contra un penetrómetro; permitiría usar 300 y 450 mm y una escala absoluta. Solo se documenta.
11. **Demo de cajas**: dos cajas de tierra del mismo origen, una suelta y otra compactada a mano, dos puntos por caja para cumplir A-FLD-04 en una sola sesión. La sesión grabada se guarda como fixture y un test verifica el orden (compactada mayor). Si no se cumple, se repite la toma; nunca se corrigen los números.

## Supuestos introducidos

| Id | Descripción | Valor de ejemplo | Fuente |
|---|---|---|---|
| A-FLD-01 | Golpes mínimos válidos por punto y descarte del primer golpe como asentamiento | 4 válidos, descartar el primero | criterio del equipo (práctica de impactómetros) |
| A-FLD-02 | Configuración del martillador v0: frecuencia mínima, masa del carro, alturas del accesorio y altura estándar de v0 | 100 Hz; ~2 kg; 150, 300 y 450 mm; v0 150 mm | criterio del equipo (master doc) |
| A-FLD-03 | Coeficiente de variación máximo del pico en un punto | 0.3 | criterio del equipo |
| A-FLD-04 | Puntos OK mínimos para normalizar una sesión | 3 | criterio del equipo |
| A-FLD-05 | El índice relativo se interpreta como dureza superficial relativa dentro del lote ese día, proxy cualitativo de compactación superficial, no calibrado | n/a | pendiente AFA |
| A-FLD-06 | Tolerancia de días hacia atrás para tomar SMAP L4 en la tarjeta | 3 días | criterio del equipo |

## Risks / Trade-offs

- [DeviceMotion limitado a ~60 Hz en algunos navegadores] → se mide la frecuencia efectiva y se rechaza con mensaje claro; en ese caso la feature queda como demostración guiada.
- [iOS exige permiso explícito y HTTPS] → botón de permiso en la pantalla de captura; deploy en Vercel ya es HTTPS.
- [Saturación del acelerómetro] → duración del pulso como segunda métrica y golpes marcados.
- [Que se lea como medición calibrada] → limitaciones en cada respuesta, texto "relativo, no calibrado" en la UI y sin efecto en el motor.

## Supuestos abiertos para AFA

- ¿La compactación superficial es un problema que hoy los haga cambiar la rotación (por ejemplo, sumar gramíneas o servicio)?
- ¿Qué herramienta usan hoy (penetrómetro, pala) y a qué profundidad está el problema típico?
- ¿Les serviría el índice relativo para elegir dónde hacer una medición más seria?

## Open Questions

- Material del riel o tubo y fijación del celular al carro: se decide en el evento, no cambia el spec (masa y alturas ya están fijadas en A-FLD-02).
