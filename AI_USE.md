# Uso de IA en este proyecto

Declaración de transparencia para el jurado de NASA Space Apps Challenge 2026 (sede Rosario).

## Qué herramientas usamos

- **Claude Code (Anthropic)** como asistente de ingeniería: redacción de specs con OpenSpec, implementación de código, tests y documentación, siempre bajo revisión del equipo.

## Dónde NO hay IA

- **El motor de decisión es 100 % determinista.** No usa modelos de lenguaje, ni aleatoriedad, ni red. Misma entrada, misma salida byte a byte (hay tests que lo verifican).
- **Las explicaciones se generan con plantillas deterministas** a partir de la salida del motor. Cada número del texto proviene de un dataset, de un dato del usuario o de un supuesto marcado.

## Dónde SÍ puede haber IA en el producto

- **Agente "Preguntale a Rastrojo"**, en dos iteraciones. La primera (por defecto) funciona con reglas deterministas, sin modelo de lenguaje. La segunda, opcional, usa Claude (Anthropic) para entender preguntas abiertas, pero solo puede responder con lo que devuelven las tools de lectura sobre el motor; una guarda rechaza cualquier número que no venga de esas tools y, ante cualquier falla, vuelve al cerebro por reglas. Cada respuesta muestra la traza de tools usadas para poder verificarla.
- **Capa opcional en el canal WhatsApp**, apagada por defecto, que solo reformula el texto de la plantilla para que sea más conversacional. Tiene guardas: no puede agregar ni cambiar números, cultivos ni recomendaciones; ante cualquier violación o error se usa la plantilla original.

## Datos

- No se inventan datos agronómicos ni económicos. Todo valor que no viene de un dataset NASA o del usuario está registrado como supuesto en `docs/assumptions.md`, con fuente o con la marca "pendiente AFA".
