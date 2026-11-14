# Proposal: ask-agent-llm

**Prioridad:** P2 (segunda iteración del agente; entra solo si `ask-agent-scripted` está estable). Si falla o no hay clave, el agente vuelve al cerebro por reglas.

## Why

El enunciado oficial pide usar "SI" para traducir datos NASA en recomendaciones prácticas y fáciles de entender para el productor, y explicar cómo el modelo interpreta la incertidumbre y dónde hace falta validación local. Los menús alcanzan para la demo, pero un productor o un agrónomo quiere preguntar con sus palabras ("soy arrendatario por dos años, ¿me conviene meter trigo?", "¿por qué la vicia sale primera?", "¿qué pasa si el año viene seco?"). Un agente conversacional con tools propias sobre el motor determinista resuelve eso sin que el modelo calcule ni invente números.

## What Changes

- Reemplaza el cerebro por reglas de `ask-agent-scripted` por un modelo de lenguaje con el mismo contrato, el mismo catálogo de tools y la misma traza; el cerebro por reglas queda como fallback.

- Nuevo agente conversacional ("Preguntale a Rastrojo") que entiende preguntas y descripciones en lenguaje natural y responde usando solo tools de lectura sobre el motor, la caché NASA, las explicaciones y el registro de supuestos.
- Traducción de lenguaje natural a entradas estructuradas: el agente propone un perfil de actor o una rotación actual a partir de lo que cuenta el usuario y pide confirmación antes de evaluar.
- Guarda de anclaje: cada número de la respuesta tiene que aparecer en las salidas de tools del turno o en el mensaje del usuario; si no, se reintenta una vez y si no, cae a la respuesta por plantilla.
- Traza visible "cómo llegué a esto": qué tools usó, con qué parámetros y qué `input_hash` devolvió el motor.
- Fallback al cerebro por reglas de `ask-agent-scripted` sin clave, sin red, en `DEMO_MODE` o ante error.
- Canales: panel de chat en la web y texto libre en WhatsApp; los menús siguen existiendo.

## Capabilities

### New Capabilities
- `ask-agent-llm`: cerebro con modelo de lenguaje sobre el contrato de `ask-agent`, con guardas de anclaje y alcance, límites y fallback.

### Modified Capabilities
- Ninguna archivada todavía. Depende de `ask-agent` (definido en `ask-agent-scripted`). Agrega en `quality` el set de evaluación del agente y en `climate-scenarios` la comparación de enfoques estadísticos (P2).

## Impact

- Nuevo módulo `fieldshift.application.agent` y adaptadores; dependencia `anthropic` (SDK oficial de Python).
- Variables de entorno: `ANTHROPIC_API_KEY`, `AGENT_ENABLED`, `AGENT_MODEL`, `AGENT_EFFORT`, `AGENT_TIMEOUT_S`, `AGENT_MAX_TOOL_CALLS` en `.env.example` sin valores.
- `AI_USE.md` se actualiza: el agente usa un modelo de lenguaje para conversar, nunca para calcular.

## Fuera de alcance

- Que el agente calcule, estime o prediga valores, o modifique datos, caché o parámetros persistidos.
- Memoria entre sesiones, cuentas de usuario o historial guardado.
- Voz y audio (P2 futuro en WhatsApp).
- Recomendaciones de productos comerciales, dosis o marcas.
