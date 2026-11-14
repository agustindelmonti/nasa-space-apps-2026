# Brief del proyecto (Space Apps Rosario 2026 · Field Shift)

Resumen del prompt inicial del equipo. Fuente de verdad para las specs junto con `openspec/config.yaml`.

## Desafío

"Field Shift: Adapting Farms with NASA Data": herramienta de apoyo a la decisión que usa observaciones NASA + suelo local + características de cultivo + prioridades del productor para explorar rotaciones que fortalezcan la salud del suelo y adapten el campo a condiciones cambiantes.

Pide: comparar al menos 3 rotaciones incluida la actual; para cada una por qué, con qué evidencia, beneficios, qué información falta y qué riesgos; contemplar prioridades del productor; "apoya, no reemplaza" al agrónomo; explicar en lenguaje simple evapotranspiración, anomalías de humedad, NDVI, heladas y balance hídrico, y en qué difiere el dato satelital de la medición de campo. Datos sugeridos: SMAP, ECOSTRESS, GPM, Landsat, MODIS, POWER, GRACE/GRACE-FO, SRTM, GEDI.

Desafío local AgTech con AFA, eje "Gestión hídrica inteligente". Criterios: Impacto, Creatividad, Validez, Pertinencia (uso profundo y central de datos NASA), Presentación. Entregables: repo, deploy, video YouTube, página NASA, pitch 4 min con demo en vivo. Deadline domingo 15/11 15:00.

## Dominio: rotaciones en zona núcleo (siembra directa)

- Soja continua: menos capital; degrada suelo, favorece malezas.
- Maíz/soja: rastrojo de maíz mejora la soja siguiente; más capital.
- Trigo/soja 2da/maíz: dos ingresos en un año; más costo y riesgo hídrico.
- Con cultivo de servicio (vicia, centeno, avena): cobertura, carbono, malezas, raíces; costo sin ingreso y consume agua en año seco.

Mirada agronómica: MO y carbono (gramíneas aportan), N (soja fija, gramíneas consumen), malezas resistentes y plagas, agua (cada cultivo consume distinto y en distinta época; doble cultivo y servicio dependen de perfil y napa), compactación.

Mirada financiera: corto vs largo plazo, riesgo del doble cultivo, diversificación, capital de trabajo por mes, contexto variable. No hardcodear precios ni retenciones.

Actores: Propietario (largo, valor del campo), Arrendatario (corto, margen de la campaña), Agrónomo (evidencia), Cooperativa AFA (largo, socio rentable y suelo regional), Banco (repago, menor riesgo climático), Contratista (calendario de maquinaria).

Función objetivo:
```
max_r Σ_{t=1..H} E[Margen_t(r)]/(1+i)^t + α·ΔSuelo(r) − λ·Riesgo(r)
s.a. agua disponible (perfil + napa) por cultivo, capital de trabajo por mes, ventanas de siembra y maquinaria
```
E y Riesgo sobre años históricos reales del registro NASA clasificados seco/normal/húmedo (enumerados, no Monte Carlo). H, α, λ como perfiles y sliders; se muestra cómo cambia el ranking. La herramienta no decide.

## MVP

1. Motor determinista de rotaciones (actual + al menos 2 alternativas) por perfil de actor.
2. "Agua invisible": factibilidad hídrica de doble cultivo o cultivo de servicio con GRACE-FO (TWS regional) + SMAP L4 (humedad zona raíces) + GPM IMERG y POWER (lluvia, T, ET0) + NDVI histórico MODIS/HLS. Cada dato con resolución y limitación.
3. Modelo de actores (propietario, arrendatario, cooperativa, banco): mismo lote, rankings distintos.
4. Explicación estructurada por plantillas deterministas.
5. Canal WhatsApp: ubicación + rotación actual → resumen. LLM opcional solo reformula, sin agregar números, con fallback a plantilla. Si no llega, web que simula el chat contra la misma API.
6. Web de demo: mapa con capas GIBS, tabla de rotaciones, sliders de actor, panel de evidencia.

Opcional: martillador de suelo (acelerómetro del celular tipo Clegg, valores relativos no calibrados); "máquina del tiempo" solo como vista.

Lote de demo: real de zona núcleo, sur de Santa Fe, coordenadas a definir (placeholder de trabajo: zona Casilda/Zavalla, marcado ASSUMPTION). Motor sirve para cualquier punto; demo cacheada para funcionar sin internet.

## Preguntas abiertas para AFA

- Rotación actual típica de los socios y la que les gustaría hacer pero no se animan.
- Ventanas de siembra y cosecha por cultivo en sur de Santa Fe.
- Coeficientes de cultivo y umbrales de agua útil para decidir doble cultivo o cultivo de servicio.
- Rangos de rinde y costos por cultivo (parámetros, no verdad).
- Si la compactación es un dolor que cambia la rotación.

## Comunicación honesta

Apoya, no reemplaza al agrónomo. Escenarios históricos, no predicción. Resolución y limitaciones de cada dataset (GRACE-FO regional ~300 km efectivos, SMAP L4 ~9 km). Supuestos marcados. Uso de IA declarado. PolPilot solo como visión ("podría vivir dentro de PolPilot Agro").
