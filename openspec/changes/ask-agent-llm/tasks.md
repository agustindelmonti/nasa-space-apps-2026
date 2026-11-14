# Tasks: ask-agent-llm (P2)

## 1. Prerrequisito (P2)

- [ ] 1.1 Verificar que `ask-agent-scripted` está completo y sus tests en verde; reutilizar su catálogo de tools y extender `propose_profile` para aceptar campos extraídos por el modelo, con test de igualdad de perfil para el mismo relato

## 2. Agente y guardas (P2)

- [ ] 2.1 Integrar el SDK `anthropic` con el tool runner, prompt de sistema cacheable, chequeo de `stop_reason` y fallback ante `refusal`; test con cliente simulado que recorre una conversación de ejemplo
- [ ] 2.2 Implementar la guarda de anclaje con regeneración única y fallback a plantilla; tests de número inventado, número del usuario e inyección
- [ ] 2.3 Implementar límites de tools, tiempo y tokens; test de la séptima invocación y del timeout
- [ ] 2.4 Implementar la traza estructurada y su logging sin datos personales; test de que la traza reproduce el `input_hash` de POST /evaluate

## 3. Fallback (P2)

- [ ] 3.1 Implementar la delegación a `ScriptedBrain` ante falta de clave, error, refusal o timeout; tests con la red bloqueada y con cliente simulado que falla

## 4. Canales (P2)

- [ ] 4.1 Agregar streaming de la respuesta en POST /api/v1/ask cuando `mode = llm`; test de contrato que verifica que el cuerpo final no cambia respecto del no streaming

## 5. Evaluación y documentación (P2)

- [ ] 5.1 Armar un set de 20 preguntas reales (incluye pronóstico, decisión, inyección, girasol, incertidumbre) con criterios de aprobación y correrlo antes de la demo; registrar resultados en `docs/agent-eval.md`
- [ ] 5.2 Actualizar `AI_USE.md`, README y `.env.example` con el agente, sus límites y el modo básico
