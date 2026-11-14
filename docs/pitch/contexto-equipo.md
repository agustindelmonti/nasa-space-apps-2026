# PolPilot: contexto del proyecto para el equipo

14/11/2026 · Agustín. Documento vivo (editable): https://claude.ai/artifact/8Zd1nVmyxeCGHKd3aj9wW1

PolPilot compara rotaciones de cultivo para un lote de la zona núcleo contra 41 campañas reales de clima de NASA POWER y dice, según quién decide (propietario, arrendatario, cooperativa o banco), qué rotación conviene y si conviene sembrar o alquilar el campo. Está online en [rastrojo.vercel.app](https://rastrojo.vercel.app), donde la web todavía se llama Rastrojo. Este documento explica qué hace, qué no hace y por qué, para que todo el equipo pueda defenderlo frente al jurado.

## El desafío

Nos inscribimos en **Field Shift: Adapting Farms with NASA Data** (dificultad intermedia/avanzada, 1832 equipos inscriptos en el mundo al 14/11) y en el desafío local AgTech de **AFA**, eje *gestión hídrica inteligente*. Tema global 2026: *The Next Frontier*. (Todavía no creamos formalmente el equipo en la plataforma.)

**Qué pide Field Shift, en palabras del enunciado:** una herramienta de apoyo a la decisión que combine observaciones de la NASA con información local de suelo, características de los cultivos y prioridades del productor, para explorar rotaciones que mejoren la salud del suelo y adapten el campo a condiciones cambiantes.

| Pedido del desafío | Cómo lo cubre PolPilot |
| --- | --- |
| Comparar al menos 3 estrategias, incluida la actual | Compara 5 rotaciones, incluida la actual (soja continua) |
| Para cada una: por qué, evidencia, beneficios, qué falta y riesgos | Tarjeta de explicación con esas cinco secciones, generada por plantillas |
| Prioridades del productor | Perfil por rol (horizonte, peso del suelo, aversión al riesgo, capital) y sliders |
| Momentos de suelo descubierto y estaciones vulnerables | Franja mes a mes por rotación: suelo desnudo, heladas, déficit hídrico, calor |
| Patrones: temperatura, estrés térmico, lluvia, humedad, heladas, lluvia extrema | NASA POWER en el cálculo; capas de MODIS, SMAP e IMERG en el mapa |
| Explicar cómo el modelo trata la incertidumbre y dónde falta validación local | Escenarios históricos (no predicción), procedencia en cada número, supuestos con id |
| Apoya, no reemplaza al agrónomo | Leyenda fija en la web y en cada respuesta del chat |
| Sliders de escenario | Sliders de perfil y filtro por tipo de año (solo secos, normales o húmedos) |

**Criterios de evaluación:** impacto, creatividad, validez, pertinencia (uso profundo y central de datos NASA) y presentación. Los mentores nos remarcaron: novedad, ajuste al desafío, factibilidad (nada que suene mágico) y presentación. El pitch de 4 minutos es el primer filtro: si no convence, no miran el repo.

**Condiciones del evento y del equipo:**

- Entregables: repositorio, deploy, video, página del proyecto en la plataforma de la NASA (cierre: domingo 15/11 a las 24:00) y pitch de 4 minutos con demo en vivo.
- Etapa global: demo de 30 s de video o máximo 7 slides contando título e intro, todo en inglés; si no, el proyecto no es elegible.
- Todo el código se escribió durante el evento, en un repo público con licencia MIT y commits frecuentes.
- Sin código, endpoints ni prompts propietarios de PolPilot; sin secretos en el repo.
- Librerías open source declaradas en el README; uso de IA declarado (AI_USE.md).
- En el pitch: problema, solución, cómo funciona, por qué somos el equipo indicado. Sin modelo de negocio ni precios.

## El problema

El mismo lote se decide distinto según quién decide, y nadie sabe cómo viene el año que viene.

- **Distintos actores, distintos objetivos.** El propietario piensa en 10 años y en el valor del campo. El arrendatario piensa en la campaña y tiene el capital justo. La cooperativa mira varios años y el volumen. El banco mira si le devuelven el crédito.
- **Las rotaciones tienen costos y beneficios en tiempos distintos.** La soja continua pide menos capital pero degrada el suelo y favorece malezas. Maíz/soja mejora el suelo y la soja siguiente, pero necesita más capital. Trigo/soja de segunda da dos ingresos en un año pero suma costo y riesgo hídrico. Un cultivo de servicio (vicia, centeno) cubre el suelo y suma carbono, pero cuesta y no genera ingreso.
- **El agua decide.** El doble cultivo y el cultivo de servicio dependen del agua que queda en el perfil. En año seco pueden no convenir.
- **El clima del año que viene no se conoce.** Lo que sí tenemos son décadas de clima real medido.

Cifra del problema para el pitch: **[COMPLETAR con un dato verificado y su fuente]**.

## La solución

Elegís quién decide y PolPilot contesta, para ese lote, si conviene sembrar y qué rotación conviene, con los números y las razones a la vista.

1. **Quién decide**: propietario, arrendatario, cooperativa o banco.
2. **¿Me conviene sembrar?** (para el arrendatario: ¿me conviene seguir arrendando?). Titular con sí o no, la línea con el número que lo explica e indicadores: frente a alquilar, frente a barbecho, campañas en que habría convenido más alquilar, arriendo de equilibrio y agua. El arriendo (qq de soja/ha) se edita y la respuesta cambia en vivo.
3. **Rotaciones comparadas**: las 5 rotaciones por puntaje, cada una con su franja de 24 meses (cultivo, suelo desnudo, heladas), agua, cambio en el suelo, campañas con pérdida y diferencia frente a la actual. Filtros por tipo de año.
4. **Columna lateral**: mapa satelital con capas NASA (color natural, SMAP, NDVI MODIS, IMERG), panel de factibilidad hídrica y *Ajustar perfil*.
5. **Evidencia**: por qué, riesgos y qué falta saber, y el detalle completo con desglose del puntaje, procedencia y supuestos.
6. **Preguntale a PolPilot**: chat por reglas («¿me conviene sembrar?», «¿y si viene seco?») y simulador de WhatsApp, con traza de herramientas y hash.

Rotaciones del lote demo: soja continua (la actual), maíz/soja, trigo/soja de segunda → maíz, maíz/soja con centeno de servicio y soja con vicia de servicio. El lote demo tiene unas 31 ha y está al sureste de Casilda, Santa Fe.

## Cómo funciona por dentro

El motor es 100 % determinista: mismos datos, mismo resultado, sin IA, sin azar y sin red. Cada evaluación lleva un hash SHA-256 del input y la versión del motor.

1. **Clima del punto del lote**: NASA POWER diario 1981-2025 (lluvia corregida, temperaturas, radiación, viento, humedad). La radiación falta en 1981-83, así que la serie útil arranca en 1984.
2. **41 campañas reales** (1984 a 2024), clasificadas en seca, normal o húmeda por terciles de lluvia; cada campaña pesa lo mismo.
3. **Balance de agua diario FAO-56** con ET0 Penman-Monteith calculada con POWER y humedad inicial de cada campaña desde GWETROOT: factible, riesgoso o no factible. Con estrés severo o perfil sin recargar se aplica el rinde de año seco; el estrés moderado queda como riesgo.
4. **Calendario de vulnerabilidad**: heladas, déficit, calor en floración y lluvia extrema por mes.
5. **Suelo**: índice ΔSuelo de -100 a +100 (cobertura, carbono, nitrógeno, malezas, raíces), meses de suelo desnudo y lluvia sobre suelo desnudo.
6. **Economía**: margen bruto por campaña según el tipo de año; campañas con pérdida, peor año y pico de capital de trabajo.
7. **Puntaje por rol y ranking**; solo compiten las rotaciones elegibles.
8. **¿Me conviene sembrar?**: la primera rotación contra alquilar el campo y contra barbecho.
9. **Explicaciones** con plantillas fijas; un test verifica que cada número del texto exista en la salida.

## La función de optimización

Puntaje_u(r) = Margen_u(r) + α_u · ΔSuelo(r) − λ_u · Riesgo(r)

Formal: J_u(r) = AF(i_u, H_u) · Ē(r) + α_u · ΔS(r) − λ_u · AF(i_u, H_u) · ES_1/3(r), maximizado sobre las rotaciones factibles del lote.

| Factor | Qué es | De dónde sale |
| --- | --- | --- |
| Ē(r) margen esperado | Promedio del margen bruto anual en las 41 campañas | Clima: NASA POWER. Rindes, precios y costos: supuestos (A-DEMO-02 a 06), no NASA |
| AF(i, H) | Lleva el margen al horizonte y la tasa del rol (VAN) | Perfil del rol (supuesto) |
| ΔS(r) | Índice de suelo de -100 a +100 | Reglas agronómicas (supuestos) + lluvia sobre suelo desnudo (NASA POWER) |
| ES_1/3(r) riesgo | Caída media del margen en el peor tercio de las campañas | NASA POWER, campañas reales |
| α, λ | Peso del suelo y aversión al riesgo | Perfil del rol (supuesto) |
| Restricciones | Agua factible (FAO-56), capital máximo, doble cultivo y servicio permitidos | NASA POWER + perfil del rol |

| Rol | Horizonte | Tasa | α | λ | Capital máximo |
| --- | --- | --- | --- | --- | --- |
| Propietario | 10 años | 6 % | 5 | 0,3 | sin tope |
| Arrendatario | 1 año | 12 % | 0 | 0,5 | 450 USD/ha |
| Cooperativa | 5 años | 8 % | 3 | 0,5 | sin tope |
| Banco | 3 años | 10 % | 0,5 | 1,5 | 600 USD/ha |

Valores de ejemplo, pendientes de validar con AFA. Resultado real del motor: propietario y cooperativa → trigo/soja 2ª → maíz (maíz/soja muy cerca); banco y arrendatario → soja continua (las rotaciones con maíz superan su capital). Descartamos a propósito un término propio por rol y coeficientes κ de agua o ingreso: exigían inventar coeficientes sin fuente.

## Datos NASA

| Dataset | Producto | Estado | Para qué | Resolución y limitación |
| --- | --- | --- | --- | --- |
| NASA POWER | Diario por punto, incluida GWETROOT (humedad del suelo) | En el cálculo | Campañas, ET0, agua, humedad inicial de cada campaña, heladas, calor, riesgo | ~0,5°; reanálisis |
| MODIS (GIBS) | MODIS_Terra_NDVI_8Day | Solo mapa | Cobertura y vigor | 250 m |
| SMAP (GIBS) | SMAP_L4_Analyzed_Root_Zone_Soil_Moisture | Solo mapa | Humedad de raíces | ~9 km |
| GPM IMERG (GIBS) | IMERG_Precipitation_Rate | Solo mapa | Lluvia | ~0,1° |
| SMAP L4 | SPL4SMGP | Próximo (falta Earthdata) | Humedad inicial del balance | ~9 km |
| GPM IMERG | Final diario | Próximo (falta Earthdata) | Cruce con POWER, lluvia extrema | ~0,1° |
| GRACE-FO | Mascons | Próximo (falta Earthdata) | Contexto regional de agua | ~300 km, mensual |

La humedad inicial de cada campaña sale de GWETROOT de NASA POWER (escalada con A-WAT-18); SMAP L4 a 9 km queda como mejora. Los valores del panel de factibilidad hídrica para GRACE-FO y SMAP son de ejemplo; la lluvia de verano (412 mm) es real.

## Qué hace y qué no hace

| Hace | No hace |
| --- | --- |
| Compara 5 rotaciones del lote demo | No analiza cualquier lote todavía (un solo lote cacheado) |
| Usa 41 campañas reales de NASA POWER | No pronostica clima ni precios |
| Ranking distinto por rol | No modela acopio, corredor ni insumos |
| Dice si conviene sembrar o alquilar y el arriendo de equilibrio | No usa precios de mercado en vivo |
| Balance de agua FAO-56 y calendario de vulnerabilidad | No mide el lote (grilla de ~50 km) ni usa sensores |
| Procedencia en cada número | No da un «% de confianza» |
| Avisa qué datos faltan | No usa todavía SMAP, IMERG ni GRACE-FO en el cálculo |
| Chat por reglas con traza | No usa un modelo de lenguaje en el chat |
| Simulador de WhatsApp | No está conectado a WhatsApp real |
| Web en celular y proyector, API pública | Sin usuarios ni carga de lotes propios |
| Explicaciones con plantillas fijas | No modela fertilización ni el costo futuro de reponer nutrientes |

## Supuestos y validación

Unos 59 supuestos con id en `data/assumptions.yaml`, casi todos pendientes de AFA. Cada número lleva badge OBS, DER, SUP o USU. Lo más sensible: con 14 qq/ha de arriendo conviene sembrar, con riesgo, para todos los roles; el equilibrio es 21,5 qq/ha para el propietario y 16,5 para el arrendatario. Validación: AFA (rotaciones, ventanas, Kc, agua útil, rindes y costos), rindes de años secos contra MAGyP, precios de la BCR, SMAP L4 y datos de campo.

## Arquitectura y cómo correrlo

Python 3.12 + Pydantic v2 (dominio y motor), FastAPI (API), Vite + React 19 + Leaflet (web), Vercel (deploy desde main). 247 tests de Python, 32 de Vitest y 15 end-to-end en 3 tamaños de pantalla. Local: `uv sync`, `uv run pytest`, `uv run uvicorn rastrojo.adapters.api:app --port 8000`, y en `web/`: `npm ci` y `VITE_API_URL=http://localhost:8000 npm run dev`.

## Diferenciales

Revisamos 16 repos de Field Shift y 8 de Latinoamérica. Nadie modela la tenencia de la tierra ni responde «¿me conviene sembrar o alquilar?». Suma: transparencia (procedencia, supuestos con id, hash), contexto argentino (retenciones, arriendo en quintales, GeoINTA, MAGyP, BCR). Más cercanos: Surco (Bolivia, solo POWER, sin actores) y fast-app (San Luis, foco en login y lotes).

## Pitch y demo

8 slides en 4:00 (deck: https://claude.ai/artifact/APHhQmfuP6TYJRSMKqCccB). Demo en vivo: abrir la web antes; propietario con 14 qq/ha (sí, conviene sembrar con riesgo; equilibrio 21,5); cambiar a 25 qq/ha (conviene alquilar); cambiar a banco o arrendatario; si sobra tiempo, el chat.

## Preguntas probables del jurado

| Pregunta | Respuesta corta |
| --- | --- |
| ¿Predice el clima? | No: 41 campañas reales, años secos, normales y húmedos. |
| ¿Dónde está la NASA en el cálculo? | NASA POWER define campañas, ET0, agua, heladas y riesgo. |
| ¿Y SMAP, IMERG, GRACE-FO? | En el mapa y diseñados para el motor; falta Earthdata. |
| ¿Precios y rindes? | Supuestos de ejemplo con id, a validar con AFA y BCR. |
| ¿Usan IA? | Para programar (declarado). El motor y el chat son deterministas. |
| ¿Cuándo conviene alquilar? | La mejor rotación del propietario deja ~478 USD/ha por año; 14 qq ≈ 311 USD/ha. Con más de 21,5 qq conviene alquilar. |
| ¿Qué tan preciso es para mi lote? | POWER es una grilla de ~50 km; por eso combinar con datos de campo. |
| ¿Por qué ustedes? | Somos el equipo de PolPilot, que ya acompaña al productor del lote al camión; hacemos bots de WhatsApp para el agro; somos de Rosario. [COMPLETAR: perfiles] |

## Pendientes antes de la entrega

- [ ] Cifra verificada del problema (slide 2)
- [ ] Perfiles de Lucas, Agustín, Wenceslao y Luciano Raffagnini (slide 8)
- [ ] Crear el equipo en la plataforma con todos en Members
- [ ] Decidir si la web pasa a llamarse PolPilot
- [ ] GIF o video corto de la demo por si falla la red
- [ ] Página del proyecto en inglés en la plataforma de la NASA
- [ ] Versión en inglés de máximo 7 slides (o video de 30 s) para la etapa global
- [ ] Ensayar el pitch con cronómetro (4:00)

## Fuentes

- Demo: https://rastrojo.vercel.app
- Repo: https://github.com/agustindelmonti/nasa-space-apps-2026
- Desafío: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
- NASA POWER: https://power.larc.nasa.gov/ · NASA GIBS: https://gibs.earthdata.nasa.gov/ · Earthdata: https://www.earthdata.nasa.gov/
- FAO-56: https://www.fao.org/4/x0490e/x0490e00.htm · Sentinel-2 cloudless (EOX): https://s2maps.eu/
