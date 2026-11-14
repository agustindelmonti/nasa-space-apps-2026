# Tasks: whatsapp-channel

## 1. Motor conversacional (P0)

- [ ] 1.1 Modelos `Session`, `InboundMessage`, `OutboundMessage` y enum de estados; test que rechaza estado desconocido en verde
- [ ] 1.2 Tabla de transiciones con saludo, ubicación (pin, texto, DEMO, intentos inválidos) y cobertura; tests "Primer mensaje", "Pin de WhatsApp", "Texto con coma decimal", "Texto ambiguo", "Tres intentos inválidos" y "Ubicación fuera de Argentina" en verde
- [ ] 1.3 Menús de rotación y actor con `Evaluator` falso; tests "Opción válida", "Opción fuera de rango", "Elegir arrendatario" y "Transición reproducible" en verde
- [ ] 1.4 Resultado, detalle, cambiar actor, glosario y comandos globales; tests "Resultado con menú final", "Detalle de la primera rotación", "De arrendatario a propietario", "Definición de NDVI", "Reiniciar a mitad del flujo" y "Audio recibido" en verde

## 2. Simulador (P0)

- [ ] 2.1 `SimulatorAdapter` y POST /chat/simulate con sesiones `sim:`; tests "Flujo completo simulado" y "Sin texto ni ubicación" en verde con DEMO_MODE=1
- [ ] 2.2 Conectar `Evaluator` real al caso de uso de evaluación lite con formato whatsapp; verificar con TestClient que el resumen coincide con el texto WhatsApp de `explanations` para `demo-casilda`

## 3. Adaptador Twilio (P0)

- [ ] 3.1 `TwilioAdapter`: parseo del form y render TwiML; tests "Respuesta TwiML" y "Mismo flujo en dos canales" en verde
- [ ] 3.2 Validación de firma y canal deshabilitado; tests "Firma inválida" y "Canal sin configurar" en verde con vectores de firma conocidos
- [ ] 3.3 Manejo de error interno con disculpa fija; test "Error interno durante evaluación" en verde
- [ ] 3.4 Prueba manual en Twilio Sandbox con túnel o deploy: enviar "hola", pin, "1", "2" desde un teléfono y verificar el resumen recibido

## 4. Sesiones y privacidad (P1)

- [ ] 4.1 `SessionStore` en memoria con TTL, tope LRU, lock por clave y deduplicación por `MessageSid`; tests "Sesión vencida" (reloj inyectado) y "Webhook repetido" en verde
- [ ] 4.2 Logging estructurado con número hasheado y filtro de secretos; tests "Número hasheado" y "Secreto en log" en verde
- [ ] 4.3 Agregar variables al `.env.example` y verificar con un test que cada variable leída por `Settings` figura en `.env.example` sin valor

## 5. Capa LLM opcional (P2)

- [ ] 5.1 Interfaz `Rephraser` con implementación nula por defecto; test "Flag apagado" (sin llamadas de red) en verde
- [ ] 5.2 Guardas de números, cultivos, expresiones prohibidas, leyendas y largo; tests "Número agregado", "Número cambiado de formato", "Cultivo agregado" y "Recomendación agregada" en verde con un `Rephraser` falso
- [ ] 5.3 Implementación HTTP del proveedor con timeout y fallback; test "Timeout del proveedor" con servidor falso en verde
