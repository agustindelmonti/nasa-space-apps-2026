# Tasks: ask-agent-scripted (P1)

## 1. Contrato y tools (P1)

- [ ] 1.1 Definir los modelos Pydantic del contrato (`AskRequest`, `AskResponse`, `ToolTrace`, `ConversationState`) y exportar su JSON Schema; test de validación
- [ ] 1.2 Implementar el catálogo de tools sobre los casos de uso con esquemas generados desde Pydantic; tests de tool fuera de catálogo y entrada inválida

## 2. Cerebro por reglas (P1)

- [ ] 2.1 Implementar normalización, `intents.yaml` y clasificador con desempate; tests de sinónimos, sin coincidencia y determinismo
- [ ] 2.2 Implementar extractores de actor, años, riesgo, cultivos, clase de año y precio; tests de precio y girasol
- [ ] 2.3 Implementar guiones de tools por intención y plantillas de alcance, ayuda y propuesta de perfil; tests de "por qué", pronóstico, incertidumbre y arrendatario
- [ ] 2.4 Implementar la traza y verificar que reproduce POST /evaluate; test de reproducción

## 3. Canales (P1)

- [ ] 3.1 Conectar POST /api/v1/ask, el panel web y el texto libre de WhatsApp; prueba manual con las preguntas del guion de demo
