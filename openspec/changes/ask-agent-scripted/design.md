# Design: ask-agent-scripted

## Context

Ver proposal.md. Primera de dos iteraciones; la segunda es `ask-agent-llm`. Ambas comparten el contrato y el catálogo de tools que define este change, para que cambiar de cerebro no toque canales ni front.

## Goals / Non-Goals

**Goals:** contrato estable; cerebro determinista que cubra las preguntas del guion de la demo; iterar intenciones y sinónimos con AFA editando YAML.

**Non-Goals:** comprensión abierta del lenguaje; eso es `ask-agent-llm`.

## Decisions

1. **Interfaz `Brain`** con dos implementaciones: `ScriptedBrain` (este change) y `LlmBrain` (siguiente). La aplicación elige por configuración y usa `ScriptedBrain` como fallback.
2. **Tools como funciones puras de `application`** envolviendo casos de uso; mismas definiciones JSON Schema que usará el LLM (generadas desde los modelos Pydantic), para no duplicar.
3. **Clasificador:** normalización (minúsculas, sin tildes, lematización liviana por tabla), puntaje por coincidencia de palabras clave y frases de `intents.yaml`, desempate por prioridad fija declarada en el YAML. Alternativa descartada: modelo de clasificación entrenado (no determinista entre versiones y sin datos de entrenamiento).
4. **Extractores:** expresiones regulares para precios y años, léxico de cultivos con sinónimos ("poroto" = soja), léxico de actores y de actitud ante el riesgo.
5. **Mapeo de perfil:** tabla fija en YAML (tenencia × años × actitud → H, α, λ) apoyada en A-ACT-01..04 y A-ACT-07; sin valores nuevos inventados.
6. **Plantillas:** se reutilizan las de `explanations` más tres nuevas: alcance, ayuda y propuesta de perfil.

## Risks / Trade-offs

- [Preguntas no cubiertas] → intención ayuda con menú; se registran (sin datos personales) para ampliar el YAML.
- [Sinónimos regionales] → revisar el YAML con AFA.

## Open Questions

- Lista final de preguntas del guion de demo (se arma con `demo-mode`).
