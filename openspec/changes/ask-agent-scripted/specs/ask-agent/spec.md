# Spec Delta

## Purpose

Define el contrato del agente conversacional de Rastrojo (tools, respuesta, traza) y una primera implementación determinista por reglas que responde preguntas en lenguaje natural sin modelo de lenguaje.

## ADDED Requirements

### Requirement: Contrato de consulta
El agente MUST recibir el texto del usuario, el id de lote, el estado de conversación (actor y rotación confirmados, si los hay) y el canal, y MUST devolver el texto de respuesta, las cifras citadas con su procedencia, la traza de tools, el estado de conversación actualizado, sugerencias de siguiente pregunta y el modo usado (`scripted` o `llm`).

#### Scenario: Respuesta completa
- **WHEN** se consulta "¿cuál me conviene?" para el lote demo con actor propietario confirmado
- **THEN** la respuesta incluye texto, cifras con procedencia, traza con el `input_hash` de la evaluación, sugerencias y `mode = scripted`

### Requirement: Catálogo cerrado de tools de solo lectura
El agente MUST disponer solo de estas tools: contexto del lote, evaluación de rotaciones, contraste entre actores, sensibilidad a α y λ, explicación de una rotación, evidencia por dataset, consulta de supuestos, glosario, calendarios de suelo desnudo y vulnerabilidad, y propuesta de perfil. Cada tool MUST validar entrada y salida con los modelos de dominio y MUST NOT modificar datos.

#### Scenario: Tool fuera de catálogo
- **WHEN** se intenta invocar una tool que no está en el catálogo
- **THEN** se rechaza con un error tipado y no se ejecuta nada

#### Scenario: Entrada inválida
- **WHEN** se invoca la evaluación con λ negativo
- **THEN** la tool devuelve un error de validación y el agente lo explica en lenguaje simple

### Requirement: Clasificación determinista de intenciones
El cerebro por reglas MUST clasificar cada mensaje en una intención del conjunto cerrado: ranking, por qué una rotación, comparar actores, agua, suelo desnudo, heladas y vulnerabilidad, riesgo e incertidumbre, qué pasa si (precio o clase de año), glosario, supuestos, describir mi situación, ayuda. Ante empate o sin coincidencia MUST elegir ayuda. El mismo texto MUST dar siempre la misma intención.

#### Scenario: Sinónimos
- **WHEN** el usuario escribe "¿qué me rinde más?"
- **THEN** la intención es ranking

#### Scenario: Sin coincidencia
- **WHEN** el usuario escribe "¿cómo está el dólar?"
- **THEN** la intención es ayuda y la respuesta lista lo que el agente puede contestar

### Requirement: Extracción de entidades por reglas
El cerebro MUST extraer por reglas: tipo de actor (dueño, arrendatario, cooperativa, banco), años de contrato, actitud ante el riesgo, cultivos y rotación del catálogo, clase de año (seco, normal, húmedo) y precio con unidad. Los valores extraídos MUST registrarse como USER_INPUT.

#### Scenario: Precio en el mensaje
- **WHEN** el usuario pregunta "¿y si la soja vale 400 dólares la tonelada?"
- **THEN** se extrae precio de soja 400 USD/t como USER_INPUT y se reevalúa con ese parámetro

#### Scenario: Cultivo fuera de catálogo
- **WHEN** el usuario menciona girasol
- **THEN** el agente explica que el catálogo del MVP no lo incluye y ofrece seguir con las rotaciones disponibles

### Requirement: Guion de tools por intención
Cada intención MUST tener un guion fijo y documentado de tools a invocar (por ejemplo, ranking: contexto del lote y evaluación; por qué: evaluación y explicación de la rotación) y MUST responder con la plantilla correspondiente de `explanations`. El agente MUST NOT producir números que no vengan de las salidas de esas tools o del mensaje del usuario.

#### Scenario: Por qué una rotación
- **WHEN** el usuario pregunta "¿por qué la vicia sale primera?"
- **THEN** se invocan evaluación y explicación de esa rotación, y la respuesta usa la plantilla de "por qué" con sus cifras y procedencia

### Requirement: Propuesta de perfil con confirmación
Ante la intención "describir mi situación", el agente MUST proponer un perfil de actor mapeando las entidades extraídas a H, α, λ con una tabla fija basada en los perfiles predefinidos, MUST mostrarlo en palabras y MUST esperar confirmación o corrección antes de usarlo.

#### Scenario: Arrendatario por dos años
- **WHEN** el usuario escribe "alquilo por dos años y no me puedo dar el lujo de un mal año"
- **THEN** el agente propone H = 2 y aversión al riesgo alta, lo explica y pregunta si es correcto

### Requirement: Alcance y lenguaje honesto
El agente MUST NOT pronosticar el clima, garantizar resultados, dar porcentajes de confianza, recomendar productos comerciales ni decidir por el usuario. Ante esos pedidos MUST responder con la plantilla de alcance, que explica que trabaja con escenarios históricos. Toda respuesta que compare rotaciones MUST incluir las dos leyendas fijas.

#### Scenario: Pronóstico
- **WHEN** el usuario pregunta "¿va a llover el año que viene?"
- **THEN** recibe la plantilla de alcance y la oferta de ver los años secos del registro

### Requirement: Incertidumbre explicada
La intención riesgo e incertidumbre MUST responder con el rango de margen por clase de año, el conteo de años con pérdida y los supuestos con estado pendiente que más pesan, tal como los devuelve el motor, sin porcentajes de confianza.

#### Scenario: ¿Qué tan seguro es?
- **WHEN** el usuario pregunta "¿qué tan seguro es esto?"
- **THEN** la respuesta muestra rango por clase de año, años con pérdida "x de N" e ids de supuestos clave

### Requirement: Traza visible
Cada respuesta MUST incluir la traza de tools con parámetros validados, `input_hash` y `engine_version` de cada evaluación. La traza MUST reproducir el mismo resultado al reenviarla a POST /evaluate.

#### Scenario: Reproducir
- **GIVEN** la traza de una respuesta de ranking
- **WHEN** se reenvía su entrada a POST /evaluate
- **THEN** el `input_hash` y el ranking coinciden

### Requirement: Determinismo y funcionamiento sin red
El cerebro por reglas MUST ser determinista (mismo mensaje y estado, misma respuesta byte a byte) y MUST funcionar sin red ni claves, incluido `DEMO_MODE`.

#### Scenario: Dos veces igual
- **WHEN** se envía el mismo mensaje con el mismo estado dos veces
- **THEN** las respuestas serializadas son idénticas

### Requirement: Formato por canal
Las respuestas MUST estar en español rioplatense con formato numérico argentino. En WhatsApp MUST respetar el límite y la partición de `explanations`; en la web MUST mostrar badges de procedencia en las cifras citadas y las sugerencias como botones.

#### Scenario: WhatsApp largo
- **WHEN** la respuesta supera un mensaje
- **THEN** se parte con marcadores (1/2) y (2/2)
