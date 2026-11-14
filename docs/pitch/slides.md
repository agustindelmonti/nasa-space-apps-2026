# PolPilot · Pitch Space Apps Rosario 2026

Volcado de las slides del deck (texto visible y notas del orador). Deck editable: https://claude.ai/artifact/APHhQmfuP6TYJRSMKqCccB · Fuente HTML/CSS en `docs/pitch/deck/`.

## 1. cover

NASA Space Apps Challenge 2026 · Rosario  
**PolPilot**  
Qué rotación conviene en tu lote, según quién decide, medida contra 41 campañas reales de datos de la NASA.  
Desafío: Field Shift: Adapting Farms with NASA Data  
+ AgTech AFA: gestión hídrica inteligente  
The Next Frontier  
Lote demo, sureste de Casilda (Santa Fe). Imagen: Sentinel-2 cloudless 2020, EOX (contiene datos Copernicus modificados).  

**Notas del orador:** [0:15] Buenas tardes. Somos PolPilot. Tomamos el desafío Field Shift, adaptar los campos con datos de la NASA, y el desafío local de AFA de gestión hídrica. Este es un lote real, acá cerca, en Casilda. La pregunta de hoy es simple: ¿qué conviene sembrar en este lote? Y la respuesta depende de quién la hace.

---

## 2. problema

El problema  
**Un mismo lote. Cuatro decisiones distintas.**  
- **Propietario**  
Mira 10 años y cuida el suelo.  
- **Arrendatario**  
Mira esta campaña y tiene capital justo.  
- **Cooperativa**  
Mira varios años y el volumen.  
- **Banco**  
Mira el riesgo de que no se pague.  
Y nadie sabe cómo viene el año. Pero sí sabemos cómo vinieron los últimos 41.  
[COMPLETAR: una cifra verificada y local. Ej.: % de la superficie de la zona núcleo que se trabaja arrendada, o % en soja continua, con su fuente.]  

**Notas del orador:** [0:30] En el campo, el mismo lote lo miran varias personas con objetivos distintos. El dueño piensa a diez años y quiere cuidar el suelo. El arrendatario piensa en esta campaña y tiene el capital justo. La cooperativa mira varios años. El banco mira si le van a devolver el crédito. Con el mismo dato, cada uno debería decidir distinto. Y encima nadie sabe cómo viene el año que viene. Lo que sí tenemos son los últimos 41 años de clima real medidos por la NASA. [Decir aquí la cifra verificada del problema.]

---

## 3. solucion

La solución  
**Elegís quién decide y te dice si conviene sembrar, y qué.**  

**Notas del orador:** [0:30] PolPilot hace eso. Elegís quién decide, y arriba de todo te contesta en criollo: ¿me conviene sembrar? Acá, con un arriendo de 14 quintales, al propietario le conviene sembrar, con riesgo: deja 167 dólares por hectárea por año más que alquilar. Si el arriendo pasa los 21 quintales y medio, conviene alquilar. Abajo ordena cinco rotaciones del lote, cada una con su franja mes a mes: qué cultivo está, cuándo queda el suelo desnudo y dónde hay riesgo de helada. Y a la derecha el lote visto desde el satélite. [Si hay demo en vivo: cambiar de Propietario a Banco y mostrar cómo se reordena.]

---

## 4. como

Cómo funciona  
**De la NASA a una decisión, sin cajas negras.**  
NASA POWER  
- **Clima diario 1984-2024**  
Lluvia, temperatura, radiación, viento y humedad del punto del lote.  
41 campañas  
- **Años secos, normales y húmedos**  
Cada campaña real se clasifica por su lluvia.  
FAO-56  
- **Agua y márgenes por campaña**  
Balance de agua diario: si el cultivo entra, sufre o no conviene sembrarlo.  
Por rol  
- **Ranking y "¿me conviene?"**  
El mismo cálculo, pesado según quién decide.  
100 % determinista: mismos datos, mismo resultado. Sin IA en el cálculo.  

**Notas del orador:** [0:30] ¿Cómo funciona? Tomamos de NASA POWER el clima diario del punto exacto del lote: lluvia, temperatura, radiación, viento y humedad, desde 1984. Con eso armamos 41 campañas reales y clasificamos cada una en seca, normal o húmeda. Para cada rotación corremos un balance de agua diario con el método FAO-56, el estándar de la FAO: nos dice si el cultivo tiene agua, si sufre o si directamente no conviene sembrarlo. De ahí salen márgenes campaña por campaña, y al final los pesamos según quién decide. Es todo determinista: mismos datos, mismo resultado. No hay IA adivinando.

---

## 5. ecuacion

La función que elige la rotación  
Puntaje(r) = Margen + α·ΔSuelo − λ·Riesgo  
Gana la rotación r con mayor puntaje entre las factibles. α, λ y el horizonte cambian según quién decide.  
- **Margen**  
Cuánto deja por hectárea en las 41 campañas, llevado al horizonte y la tasa del rol.  
NASA POWER: lluvia, temperatura, radiación  
Rindes, precios y costos: supuestos a validar con AFA y BCR (no NASA)  
- **ΔSuelo**  
Si la rotación mejora o empeora el suelo: cobertura, carbono, nitrógeno, malezas, raíces.  
NASA POWER: lluvia sobre suelo desnudo  
Reglas agronómicas: supuestos registrados  
- **Riesgo**  
Cuánto cae el margen en el peor tercio de las campañas reales. No es un pronóstico.  
NASA POWER: 41 campañas 1984-2024  
- **Factible si…**  
Hay agua para el cultivo, alcanza el capital del rol y se respetan las reglas de rotación.  
NASA POWER → ET0 y balance FAO-56  

**Notas del orador:** [0:45] Esta es la función que elige la rotación. Tres términos. El margen: cuánta plata deja por hectárea en las 41 campañas reales, llevada al horizonte de cada uno. ΔSuelo: si la rotación mejora o empeora el suelo. Y el riesgo: cuánto cae el margen en el peor tercio de los años. Lo importante es que α y λ, y el horizonte, cambian según quién decide: el dueño le da peso al suelo, el arrendatario no, el banco castiga mucho el riesgo. ¿De dónde sale cada cosa? El clima, de NASA POWER. Rindes, precios y costos hoy son supuestos que vamos a validar con AFA y la Bolsa de Comercio; no son de la NASA y lo decimos en la pantalla. Y solo compiten las rotaciones factibles: que tengan agua según el balance FAO-56 y que le alcance el capital a quien decide.
(Versión formal, por si preguntan: el margen es el VAN de los márgenes esperados, factor de anualidad por el margen medio; el riesgo es el expected shortfall del tercio inferior.)

---

## 6. roles

Mismo lote, cuatro roles  
**Mismo dato. Otra decisión.**  
| Rol | Horizonte | Suelo α | Riesgo λ |
| --- | --- | --- | --- |
| Propietario | alto | alto | bajo |
| Arrendatario | bajo | nulo | medio |
| Cooperativa | medio | medio | medio |
| Banco | medio | bajo | alto |
Propietario  
Trigo / Soja 2ª → Maíz  
Mira más años y valora el suelo.  
Cooperativa  
Trigo / Soja 2ª → Maíz  
Banco  
Soja continua  
Castiga el riesgo y limita el capital.  
Arrendatario  
Soja continua  
Para lo demás no le alcanza el capital.  

**Notas del orador:** [0:35] Y acá está la gracia. Mismo lote, mismos 41 años de datos. Para el propietario y la cooperativa gana trigo, soja de segunda y maíz: miran más años, valoran el suelo y aprovechan dos cosechas. Para el banco gana soja continua: castiga el riesgo y con su tope de capital las rotaciones con maíz no entran. Y al arrendatario directamente no le alcanza el capital de trabajo para las rotaciones con maíz, así que su única opción es soja. No lo inventamos para la slide: es lo que devuelve el motor hoy, y lo pueden ver en vivo. Los pesos de cada rol son valores de ejemplo que vamos a validar con AFA.

---

## 7. factibilidad

Factibilidad  
**Funciona hoy. Lo que no medimos, lo decimos.**  
41  
campañas reales de NASA POWER en el cálculo  
5  
rotaciones del lote demo comparadas  
324  
tests automáticos en verde (motor, API y web)  
1  
hash por evaluación: mismo input, mismo resultado  
Online: web y API en rastrojo.vercel.app  
Cada supuesto con id, a revisar con AFA  
Humedad del suelo de cada campaña: NASA POWER (GWETROOT)  
Validación: rindes por año seco contra MAGyP  

**Notas del orador:** [0:30] ¿Es real? Sí. Está online. Usa 41 campañas reales de NASA POWER, compara cinco rotaciones y tiene 324 tests automáticos. Cada evaluación lleva un hash: mismo input, mismo resultado, auditable. Y algo que nos importa: lo que no medimos, lo decimos. Cada supuesto tiene un id para revisar con AFA, la humedad del suelo al inicio de cada campaña sale de NASA POWER, y cuando falta un dato, como la napa o SMAP a 9 km, el motor lo avisa en vez de inventarlo. Para validar, vamos a contrastar los rindes de años secos contra los rindes departamentales del MAGyP.

---

## 8. equipo

Por qué somos el equipo indicado  
**Ya hacemos software para el campo.**  
01  
- **PolPilot ya existe**  
Nuestro producto acompaña al productor del lote al camión. Esto le suma el satélite a algo que ya existe.  
02  
- **Llegamos por donde el productor ya está**  
Ya hacemos bots de WhatsApp para el agro: el chat de la demo es la puerta de entrada.  
03  
- **Somos de acá**  
Rosario, al lado de los lotes que modelamos. Podemos validar con AFA y con productores la semana que viene.  
- **Lucas**  
[COMPLETAR perfil]  
- **Agustín**  
[COMPLETAR perfil]  
- **Wenceslao**  
[COMPLETAR perfil]  
- **Luciano**  
[COMPLETAR perfil]  
Próximo paso: sumar SMAP, IMERG y GRACE-FO al cálculo, validar los supuestos con AFA y abrirlo a acopios y vendedores de insumos.  

**Notas del orador:** [0:25] ¿Por qué nosotros? Porque esto no arranca de cero. Somos el equipo de PolPilot, un producto que ya acompaña al productor del lote al camión. Ya hacemos bots de WhatsApp para el campo, y por eso el chat de la demo es la puerta de entrada natural. Y somos de acá, de Rosario: podemos sentarnos con AFA y con productores la semana que viene para validar cada supuesto. [Presentar en una frase a Lucas, Agustín, Wenceslao y Luciano Raffagnini, con su perfil: software, electrónica, economía, hardware.] Lo que sigue: sumar SMAP, IMERG y GRACE-FO al cálculo y abrirlo a acopios e insumos. Gracias.

---

## 9. referencias

Referencias  
| Dataset | Producto o capa | Uso | Link |
| --- | --- | --- | --- |
| NASA POWER | Diario por punto: PRECTOTCORR, T2M, radiación, viento, humedad, GWETROOT (humedad del suelo) | En el cálculo | power.larc.nasa.gov |
| NASA GIBS · MODIS | MODIS_Terra_NDVI_8Day | Mapa | gibs.earthdata.nasa.gov |
| NASA GIBS · SMAP | SMAP_L4_Analyzed_Root_Zone_Soil_Moisture | Mapa | gibs.earthdata.nasa.gov |
| NASA GIBS · GPM | IMERG_Precipitation_Rate | Mapa | gibs.earthdata.nasa.gov |
| SMAP L4 | SPL4SMGP sm_rootzone, celda de 9 km del lote (OPeNDAP) | Evidencia y panel (hoy) | nsidc.org/data/spl4smgp |
| GRACE / GRACE-FO | JPL Mascons RL06.3 CRI, lwe_thickness | Evidencia y panel | podaac.jpl.nasa.gov |
| GPM IMERG | Final diario | Próximo | gpm.nasa.gov |
| Imagen base (no NASA) | Sentinel-2 cloudless 2020, EOX | Mapa | s2maps.eu |
Uso de IA. Desarrollamos con asistencia de Claude Code (Anthropic) para especificación e implementación, bajo revisión del equipo. El motor de decisión es 100 % determinista y no usa modelos de lenguaje. El chat de la demo responde por reglas, sin LLM. Detalle en AI_USE.md del repositorio.  

**Notas del orador:** Slide de respaldo, no se presenta. Lista cada dataset de la NASA, qué producto o capa usamos, si entra al cálculo o solo al mapa, y el link. Abajo, la declaración de uso de IA.

---
