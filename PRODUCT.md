# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Vite + React + Leaflet para la web (deploy en Vercel), API FastAPI en Python 3.12 (Render o Fly). Capas de mapa vía NASA GIBS WMTS. Canal WhatsApp vía Twilio Sandbox, con simulador de chat dentro de la web.

## Users

- **Jurado de NASA Space Apps (sede Rosario y global) y referentes de AFA**, mirando una demo en vivo de 4 minutos proyectada en un aula de UCEL. Tienen que entender en segundos qué se compara, con qué datos y por qué cambia el ranking.
- **Productor de zona núcleo pampeana** (propietario o arrendatario), que en la vida real consultaría desde el celular o por WhatsApp, con poca experiencia en geoespacial.
- **Agrónomo asesor**, que necesita evidencia trazable para defender una recomendación ante quien paga.

## Product Purpose

Rastrojo compara al menos tres rotaciones de cultivo para un lote de la zona núcleo (incluida la actual) contra años históricos reales del registro NASA, y muestra para cada una por qué, con qué evidencia, qué beneficios, qué información falta y qué riesgos. El éxito es que el productor y su agrónomo puedan discutir con datos cuánto margen de hoy conviene invertir en el suelo de mañana.

## Positioning

El mismo lote da rankings distintos según quién decide (propietario, arrendatario, cooperativa, banco), porque cada actor tiene otro horizonte, otro peso del suelo y otra aversión al riesgo. Ningún otro equipo de Field Shift modela la tenencia de la tierra, usa GRACE-FO junto con SMAP L4 para decidir doble cultivo o cultivo de servicio, ni llega al productor por WhatsApp.

## Operating Context

- Demo proyectada (1920×1080 y 1280×720) en un aula con luz ambiente, conectada o sin red (modo demo con fixtures).
- Lote de demo en el sur de Santa Fe (coordenadas a confirmar con el equipo).
- Conversación por WhatsApp: ubicación del lote, rotación actual, actor, resumen en texto.
- Opcional: martillador de suelo con el acelerómetro del celular como dato de campo frente al dato satelital.

## Capabilities and Constraints

- Motor 100 % determinista; la web solo presenta, nunca calcula puntajes.
- Cada número lleva procedencia OBSERVED, DERIVED, ASSUMPTION o USER_INPUT, visible en la interfaz.
- Escenarios históricos, no predicción. Nunca mostrar "% de confianza".
- Supuestos registrados en `docs/assumptions.md`, pendientes de validación con AFA.
- Español rioplatense en toda la interfaz; formato numérico argentino (coma decimal).

## Brand Commitments

- Nombre: **Rastrojo**. Mundo visual elegido por el equipo: **carta de suelo** (cartografía de suelos INTA/IGN impresa, papel y tinta, horizontes de suelo).
- Leyendas fijas: "Apoya, no reemplaza al agrónomo" y "Escenarios históricos, no predicción".
- PolPilot se menciona solo como visión ("este módulo podría vivir dentro de PolPilot Agro"); sin su marca en la interfaz.

## Evidence on Hand

- Datasets NASA planificados: POWER, SMAP L4, GPM IMERG, GRACE-FO, MODIS/HLS NDVI, SRTM (P1), ECOSTRESS (P2).
- No hay todavía testimonios, clientes ni métricas de uso: no inventarlos. Los valores económicos de la demo son ejemplos marcados (A-DEMO-NN).

## Product Principles

1. Mostrar la tensión entre actores, no esconderla: el cambio de ranking es el mensaje.
2. Todo número tiene origen y se puede rastrear con un toque.
3. Lo que falta se dice ("desconocido", "faltante"), nunca se rellena.
4. Lenguaje del campo antes que jerga satelital; la jerga se explica en el glosario.

## Accessibility & Inclusion

- Contraste WCAG AA mínimo, pensado para proyector con luz ambiente.
- Estados nunca codificados solo por color (siempre texto o patrón).
- Navegable con teclado; respeta movimiento reducido.
