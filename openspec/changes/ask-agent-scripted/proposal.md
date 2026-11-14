# Proposal: ask-agent-scripted

**Prioridad:** P1 (después de la demo de punta a punta del sábado; entra en la demo del domingo). Es la primera iteración del agente: sin modelo de lenguaje, determinista y testeable sin red.

## Why

El enunciado pide usar "SI" para traducir los datos en respuestas prácticas para el productor, y queremos que pueda preguntar con sus palabras. Antes de depender de un modelo de lenguaje, fijamos el contrato del agente (catálogo de tools, API `/ask`, traza, formato por canal) con un "cerebro" hecho con reglas. Así la web y WhatsApp se integran desde ya, iteramos las preguntas reales con AFA, y la segunda iteración (`ask-agent-llm`) solo cambia el cerebro.

## What Changes

- Contrato del agente: request y respuesta de `/ask`, traza de tools, formato por canal.
- Catálogo cerrado de tools de solo lectura sobre los casos de uso existentes (evaluar, contrastar actores, sensibilidad, explicar, evidencia, supuestos, glosario, calendarios, proponer perfil).
- Cerebro con reglas: clasificador determinista de intenciones (palabras clave y sinónimos en YAML), extracción de entidades por reglas (actor, años de contrato, actitud ante el riesgo, cultivos, rotación, clase de año, precio) y un guion fijo de tools por intención.
- Respuestas por plantillas de `explanations`, con leyendas, procedencia y explicación de la incertidumbre.
- Propuesta de perfil a partir del relato con confirmación antes de evaluar.

## Capabilities

### New Capabilities
- `ask-agent`: contrato conversacional, catálogo de tools, traza y cerebro determinista por reglas.

### Modified Capabilities
- Ninguna archivada. Se agregan requisitos en `api` (POST /api/v1/ask), `whatsapp-channel` (texto libre), `web-demo` (panel de chat) y `quality` (tests del agente).

## Impact

- Módulo `rastrojo.application.agent` con `tools`, `brain/scripted` y `contract`; YAML de intenciones y sinónimos versionado en el repo.
- Sin dependencias nuevas ni claves.

## Fuera de alcance

- Modelo de lenguaje (lo agrega `ask-agent-llm`).
- Memoria entre sesiones, voz, recomendaciones de productos comerciales.
