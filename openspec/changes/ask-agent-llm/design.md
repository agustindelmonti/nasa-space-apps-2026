# Design: ask-agent-llm

## Context

Ver proposal.md. El motor (`rotation-engine`), las explicaciones (`explanations`) y la API (`api`) ya están especificados y son deterministas. `ask-agent-scripted` ya definió el contrato, el catálogo de tools (con esquemas generados desde Pydantic) y la interfaz `Brain`; este change agrega `LlmBrain`, sin tocar el motor ni los canales. Los tests de determinismo de `quality` siguen corriendo sobre el motor y las tools; el texto del agente queda fuera de esa garantía y eso se declara.

## Goals / Non-Goals

**Goals:** preguntas en lenguaje natural ancladas en el motor; traducir descripciones a entradas validadas con confirmación; traza verificable; demo robusta aunque el proveedor falle.

**Non-Goals:** memoria persistente, multiagente, voz, ajuste fino de modelos.

## Decisions

1. **Modelo y SDK.** SDK oficial `anthropic` para Python, con el tool runner beta (`client.beta.messages.tool_runner` y `@beta_tool`) para el ciclo de tools; modelo por defecto `claude-opus-5-5` configurable con `AGENT_MODEL`, `output_config.effort` configurable (`AGENT_EFFORT`, por defecto `medium`, bajar a `low` si la latencia de la demo lo pide), streaming hacia la web. Fallback del lado del servidor ante `refusal` con `fallbacks: "default"` (beta `server-side-fallback-2026-07-01`), y chequeo de `stop_reason` antes de leer el contenido. Alternativa descartada: Agent SDK o Managed Agents (no hace falta sandbox ni archivos; el runner con tools propias alcanza y lo hosteamos con la API).
2. **Tools compartidas.** Se reutilizan las tools y esquemas de `ask-agent-scripted`, con `strict: true` en las definiciones. `tool_choice` en `auto` (el modelo no admite forzar tools) y el prompt de sistema nombra qué tool usar para cada tipo de pregunta.
3. **Propuesta de perfil determinista.** `propose_profile` no la decide el modelo libremente: el modelo extrae campos semánticos (tenencia, años de contrato, actitud ante el riesgo, prioridad de suelo) y la tool los mapea a H, α, λ con una tabla fija basada en los perfiles predefinidos (A-ACT-01..04, A-ACT-07). Así el mismo relato produce el mismo perfil.
4. **Guarda de anclaje reutilizada.** Se usa `parse_ar_numbers` y la lista cerrada de excepciones de `explanations`, igual que la guarda de reformulación de `whatsapp-channel`. El conjunto permitido es la unión de números en las salidas de tools del turno y en el mensaje del usuario. Una regeneración con el detalle del número rechazado; después, plantilla.
5. **Prompt de sistema estable y cacheable.** Reglas, catálogo de tools y glosario resumido van en un prefijo fijo con `cache_control`; el contexto del lote va después. Nada de fecha ni ids variables en el prefijo.
6. **Traza.** Cada invocación se registra con nombre, parámetros validados, `input_hash`, `engine_version`, duración y resultado de las guardas; se devuelve junto con la respuesta y se loguea sin datos personales.
7. **Fallback.** `LlmBrain` delega en `ScriptedBrain` ante cualquier falla; el contrato no cambia.
8. **Comparación de enfoques estadísticos (P2, en `climate-scenarios`).** Además de terciles, un agrupamiento k-means determinista (semilla fija, inicialización ordenada) sobre lluvia de ventana, ET0 y días con helada, con un reporte de coincidencia contra terciles. El agente puede explicar ambos y por qué el motor usa terciles (más simple y auditable). Responde al pedido del enunciado de comparar enfoques.

## Risks / Trade-offs

- [Latencia del modelo en vivo] → streaming, effort configurable, límite de tools por turno y preguntas de la demo probadas antes; plan B con el cerebro por reglas.
- [El modelo omite llamar a una tool y responde de memoria] → la guarda de anclaje rechaza números sin fuente; el prompt exige usar tools para cualquier cifra.
- [Costo] → tope de tokens por turno y rate limit por sesión; caché de prompt para el prefijo fijo.
- [Falsos rechazos de la guarda] → se loguea el motivo para ajustar excepciones; el fallback siempre es correcto.
- [Texto no determinista] → declarado en README y AI_USE; la traza permite reproducir los números con POST /evaluate.

## Open Questions

- Si para la demo conviene `effort: low` por latencia; se decide midiendo con las preguntas del guion.
