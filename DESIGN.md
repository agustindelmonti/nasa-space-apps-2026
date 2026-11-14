---
name: Rastrojo
description: Comparador de rotaciones con datos NASA para la zona núcleo, con el lenguaje de un visor de imagen satelital oscuro y mate.
colors:
  # Superficies (grafito mate)
  graphite: "#121517"
  panel: "#1A1E21"
  panel-2: "#22282C"
  rule: "#2F363B"
  map-ground: "#0B0D0E"
  # Texto
  text: "#ECE8E0"
  text-soft: "#A7AEB2"
  text-faint: "#7F878C"
  # Marca y agua
  straw: "#D8B46A"
  water: "#5FB4D0"
  # Estados hídricos (siempre con palabra o patrón)
  state-feasible: "#79C27A"
  state-risky: "#E8913F"
  state-not-feasible: "#EE6650"
  state-unknown: "#9AA1A6"
  # Series de cultivos (franja de campañas)
  crop-soy: "#8DBF5A"
  crop-maize: "#E6C34A"
  crop-wheat: "#C98D4B"
  crop-vetch: "#A88BC9"
  crop-rye-oat: "#5FA894"
  bare-soil: "#2C3236"
  bare-hatch: "#3E464B"
typography:
  display:
    fontFamily: "'Schibsted Grotesk', 'Helvetica Neue', Arial, sans-serif"
    fontSize: "4rem"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "'Schibsted Grotesk', 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  title:
    fontFamily: "'Schibsted Grotesk', 'Helvetica Neue', Arial, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'IBM Plex Mono', ui-monospace, monospace"
    fontSize: "0.78rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0.06em"
  figure:
    fontFamily: "'IBM Plex Mono', ui-monospace, monospace"
    fontSize: "1.25rem"
    fontWeight: 500
    lineHeight: 1.2
rounded:
  none: "0px"
  sm: "2px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "14px"
  lg: "24px"
  xl: "36px"
  xxl: "56px"
components:
  button-primary:
    backgroundColor: "{colors.straw}"
    textColor: "{colors.graphite}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
    height: "46px"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
    padding: "12px 18px"
    height: "46px"
  segmented-selected:
    backgroundColor: "{colors.straw}"
    textColor: "{colors.graphite}"
    height: "46px"
  segmented-idle:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    height: "46px"
  layer-chip:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text-soft}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
    height: "36px"
  layer-chip-on:
    backgroundColor: "{colors.straw}"
    textColor: "{colors.graphite}"
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    padding: "14px"
  ranking-row:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.text}"
    padding: "14px"
  badge-observed:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.water}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "5px 8px"
  badge-assumption:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.straw}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "5px 8px"
---

# Design System: Rastrojo

## Overview

**Creative North Star: "El lote visto desde el satélite"**

Rastrojo se ve como un visor de imagen satelital trabajado con oficio: una sala oscura y mate donde la imagen real del campo pampeano, con su mosaico de lotes, es lo más luminoso de la pantalla, y los datos se superponen con la precisión de una carta técnica. Es una herramienta de trabajo (modo Operate): navegación, controles y tablas son los estándar de la web. El mundo satelital aporta tipografía, paleta, densidad y un gesto propio; nunca disfraza la interfaz de consola, radar o cabina.

Está pensada primero para el proyector de la demo (1920×1080 y 1280×720) y después se adapta al celular. El fondo grafito mate deja que la imagen y las series de cultivos brillen solas; el dorado del rastrojo marca lo importante (lote seleccionado, actor activo, primera posición del ranking) y el celeste se reserva para el agua. La densidad es alta pero ordenada: zonas separadas por filetes de 1 px, sin tarjetas.

El gesto propio es doble: **la imagen real del lote con su contorno dorado** y **la franja de campañas**, donde cada rotación es una tira de meses con cultivos en color, suelo desnudo rayado y marcas de helada encima. Cuando cambia el actor, el ranking se reordena con un movimiento corto y flechas ▲▼ que dicen cuántos puestos subió o bajó cada rotación.

**Key Characteristics:**
- Grafito mate, nunca negro puro; texto blanco cálido, nunca blanco puro.
- La imagen satelital real del lote como protagonista de la vista principal.
- Dorado de rastrojo como única marca; celeste solo para agua.
- Filetes de 1 px y aire en lugar de tarjetas y sombras.
- Íconos de trazo fino donde ayudan a escanear, nunca como decoración.
- Movimiento con propósito: pocos momentos, cortos, que explican un cambio.

## Colors

Grafito mate con una marca dorada, un celeste reservado para agua y series de cultivos saturadas que se leen sobre oscuro.

### Primary
- **Rastrojo** (#D8B46A): marca. Contorno del lote, actor seleccionado, capa activa, primera posición del ranking (filete izquierdo de 3 px solo en esa fila), foco de teclado, selección de texto al 35 %. Texto oscuro sobre dorado da 9,3:1.

### Secondary
- **Agua** (#5FB4D0): todo lo que habla de agua o viene del satélite como observación: badge OBSERVED, panel "Factibilidad hídrica", capa SMAP, balance hídrico. 7,8:1 sobre grafito.

### Neutral
- **Grafito** (#121517): fondo de página.
- **Panel** (#1A1E21) y **Panel 2** (#22282C): zonas de trabajo y estados hover.
- **Filete** (#2F363B): líneas divisorias de 1 px.
- **Fondo de mapa** (#0B0D0E): detrás de la imagen mientras carga.
- **Texto** (#ECE8E0, 15:1), **Texto suave** (#A7AEB2, 8,2:1), **Texto tenue** (#7F878C, 5:1, solo etiquetas de meses y metadatos).

### Estados hídricos
- **Factible** (#79C27A), **Riesgoso** (#E8913F), **No factible** (#EE6650), **Desconocido** (#9AA1A6). Siempre con su palabra al lado; en la franja y en el mapa, con patrón (liso, rayado, cruzado, punteado).

### Series de cultivos
- Soja (#8DBF5A), maíz (#E6C34A), trigo (#C98D4B), vicia (#A88BC9), centeno y avena (#5FA894), suelo desnudo (#2C3236 con rayado diagonal #3E464B).

### Named Rules
**La regla de la imagen primero.** Nada en la interfaz es más luminoso ni más saturado que la imagen satelital. Si un elemento compite con ella, se apaga.

**La regla del celeste único.** El celeste es agua. Ningún botón, link ni acento decorativo es celeste.

**La regla de la leyenda.** Todo color con significado tiene leyenda visible en la misma vista.

## Typography

**Display Font:** Schibsted Grotesk (con Helvetica Neue, Arial)
**Body Font:** Atkinson Hyperlegible Next (con Atkinson Hyperlegible, system-ui)
**Label/Mono Font:** IBM Plex Mono, para cifras, unidades, coordenadas, etiquetas de capa y metadatos de dataset

**Character:** una grotesca de diario con peso para los títulos, una sans diseñada para leerse bien a distancia para todo lo operativo, y una mono para lo que es medición. Las tres son OFL y se autoalojan.

### Hierarchy
- **Display** (800, 4rem, 0,98, -0,02em): nombre del producto en la cabecera. Una vez.
- **Headline** (800, 1,75rem, 1,1): títulos de zona ("Rotaciones comparadas", "Evidencia").
- **Title** (600, 1,15rem, 1,2): nombre de cada rotación.
- **Body** (400, 1,0625rem, 1,5): explicaciones; medida máxima 68ch.
- **Label** (Plex Mono 500, 0,78rem, 0,06em, mayúsculas): nombres de capa, dataset y ejes. Es medición y metadato, no adorno.
- **Figure** (Plex Mono 500, 1,25rem, cifras tabulares): USD/ha, mm, m³/m³, años. Unidad en Texto suave y más chica.

### Named Rules
**La regla de la cifra con unidad.** Ninguna cifra sin unidad ni sin procedencia a mano. Formato argentino: coma decimal, punto de miles.

## Layout

Grilla de 12 columnas, ancho máximo 1320 px, gutter de 24 px. Vista principal en proyector: imagen del lote a la izquierda (7 columnas) con selector de capas arriba y pie de resolución y limitación abajo; a la derecha (5 columnas), de arriba hacia abajo: panel "Factibilidad hídrica" (GRACE-FO, SMAP, POWER en tres celdas), selector de actor con sus parámetros, y ranking con franjas. Debajo, a todo el ancho, evidencia y procedencia de la rotación seleccionada. El simulador de WhatsApp entra como panel lateral derecho que empuja el contenido.

En celular (390 px): actor, ranking con franjas compactas, imagen del lote, factibilidad hídrica, evidencia. Ritmo vertical en múltiplos de 4 px; más espacio sobre un título que debajo.

## Elevation & Depth

Plano y mate. La profundidad se marca con tono (grafito, panel, panel 2) y filetes. Lo único que flota (tooltips de procedencia, etiqueta del lote sobre la imagen, panel de chat) lleva fondo grafito al 85 % sobre la imagen y una sombra corta: `box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35), 0 1px 3px rgba(0, 0, 0, 0.3)`. Sin brillos, halos ni vidrio esmerilado.

### Named Rules
**La regla del mate.** Nada brilla. Ni glow, ni neón, ni degradados, ni glassmorphism.

## Shapes

Esquinas rectas en zonas y tablas (0 px), 2 px en botones, chips, badges y campos. Puntos de estado circulares de 9 px. El contorno del lote en la imagen es un polígono real con trazo dorado de 2 px y relleno dorado al 12 %; la etiqueta del lote es un rectángulo con borde dorado unido al lote por una línea de 1 px, como una anotación de carta.

## Iconography

Usamos íconos donde ayudan a escanear o a reconocer algo de un vistazo, **sin abusar**: como máximo un ícono por etiqueta, y nunca un ícono solo sin texto, salvo en controles universales (cerrar, menú) con `aria-label`.

- **Librería:** Lucide (licencia ISC), trazo de 1,5 px, tamaño 16 px junto a texto Body y 20 px en controles. Un solo set; no se mezclan librerías.
- **Color:** heredan el color del texto que acompañan (`currentColor`). Solo los íconos de estado toman el color del estado.
- **Dónde sí:**
  - Selector de capas: `satellite` (color natural), `droplets` (SMAP raíces), `scan-line` (suelo desnudo), `cloud-rain` (lluvia).
  - Panel "Factibilidad hídrica": `waves` (GRACE-FO), `droplets` (SMAP), `cloud-rain` (POWER/IMERG).
  - Selector de actor: `house` (propietario), `key-round` (arrendatario), `users` (cooperativa), `landmark` (banco).
  - Estados hídricos junto a su palabra: `circle-check` (factible), `triangle-alert` (riesgoso), `circle-x` (no factible), `circle-help` (desconocido).
  - Riesgos: `snowflake` (helada), `thermometer-sun` (estrés térmico), `sprout` (cultivo), `bug` (malezas y plagas).
  - Procedencia en tooltips: `satellite` (OBSERVED), `calculator` (DERIVED), `flask-conical` (ASSUMPTION), `user-round` (USER_INPUT).
  - Acciones: `message-circle` (abrir chat), `book-open` (glosario), `file-down` (ficha), `rotate-ccw` (reiniciar).
- **Dónde no:** títulos de sección, nombres de rotación, cifras, párrafos de explicación, ni como viñetas de lista.
- En la franja de campañas, la helada se marca con el rombo de trazo (no con un ícono completo) para no ensuciar la tira.

## Motion

Pocos momentos, cortos y con propósito: el movimiento explica un cambio de estado, nunca decora. Todo parte de un estado visible (nada empieza en opacidad 0 esperando un scroll) y todo respeta `prefers-reduced-motion`.

**Tokens:**
- Duraciones: `instant` 120 ms (hover, presionado), `quick` 200 ms (chips, tooltips), `move` 300 ms (reordenar, cambiar capa), `story` 600 ms (entrada orquestada una sola vez).
- Curva: ease-out exponencial `cubic-bezier(0.16, 1, 0.3, 1)` para todo lo que entra o se mueve; `ease-in` de 150 ms solo para lo que se va.
- Librería sugerida: Motion para React (MIT) para el reordenamiento por layout; CSS para el resto.

**Momentos autorizados:**
1. **Reordenamiento del ranking (el momento del pitch).** Al cambiar actor o slider, las filas se mueven a su nueva posición (FLIP, 300 ms) y aparece ▲ n o ▼ n en dorado durante 2,5 s. La fila que queda primera recibe el filete dorado con una transición de color de 200 ms.
2. **Cifras que cambian.** Puntaje, ΔSuelo y años con pérdida hacen una interpolación numérica de 300 ms al recalcular. No hay conteos desde cero al cargar.
3. **Cambio de capa sobre la imagen.** Fundido cruzado de 300 ms entre capas y actualización del pie de resolución.
4. **Entrada orquestada, una sola vez por sesión.** Al cargar el lote: el contorno dorado se dibuja sobre la imagen (trazo animado, 600 ms) y las franjas de campañas se llenan de izquierda a derecha con un escalonado de 30 ms por mes. Después de la primera carga, no se repite.
5. **Chat de WhatsApp.** Cada mensaje entra con desplazamiento de 8 px y fundido en 200 ms; indicador de "escribiendo" de tres puntos mientras responde la API.
6. **Carga.** Mientras la API responde, las filas del ranking mantienen su contenido anterior atenuado al 60 % con un indicador lineal fino en dorado arriba del ranking. Sin esqueletos brillantes.

**Con movimiento reducido:** sin desplazamientos ni trazos animados; los cambios son instantáneos y las flechas ▲▼ se muestran igual, porque son información.

## Components

### Buttons
- **Shape:** 2 px, alto 46 px.
- **Primary:** dorado con texto grafito. **Secondary:** panel con borde de 1 px en Filete.
- **Hover / Focus:** hover aclara el fondo un paso (120 ms); foco con anillo dorado de 2 px y 2 px de separación.

### Selector de actor
- Control segmentado estándar de cuatro opciones con su ícono y su palabra. Seleccionado: dorado con texto grafito. Debajo, los parámetros en lenguaje simple ("Horizonte 10 años · Peso del suelo alto · Aversión al riesgo media") y los sliders H, α, λ con su valor en Figure.

### Imagen del lote (componente firma)
- Imagen satelital real (Sentinel-2 o HLS vía GIBS), contorno del lote en dorado, etiqueta con superficie y coordenadas, escala gráfica calculada, selector de capas arriba y pie con dataset, resolución y limitación. Atribución del proveedor siempre visible.

### Panel "Factibilidad hídrica"
- Tres celdas con filete: GRACE-FO (anomalía de agua total, mm), SMAP L4 (humedad de raíces, m³/m³), POWER/IMERG (lluvia de la ventana, mm). Cada una con etiqueta mono, cifra grande, unidad y una línea de limitación.

### Ranking de rotaciones (componente firma)
- Tabla de filas, no tarjetas: posición, nombre, puntaje USD/ha, estado hídrico con ícono y palabra, ΔSuelo, años con pérdida "x de N", y debajo la franja de campañas con su leyenda en la cabecera. La rotación actual dice "· actual" en dorado junto al nombre.

### Franja de campañas
- 12 o 24 celdas por mes con cultivos en color, suelo desnudo rayado, rombo de helada en No factible y banda de rango histórico. Etiquetas de mes en Texto tenue.

### Badges de procedencia
- OBSERVED: celeste con borde celeste al 50 %. DERIVED: texto sobre Panel 2. ASSUMPTION: dorado con borde punteado y el id (A-WAT-01). USER_INPUT: texto con borde Texto suave. DESCONOCIDO: gris con borde de puntos. Etiqueta mono en mayúsculas; tooltip accesible por teclado con dataset, variable, período y resolución.

### Leyendas fijas
- "Apoya, no reemplaza al agrónomo" y "Escenarios históricos, no predicción" en el pie, siempre visibles.

## Do's and Don'ts

### Do:
- **Do** mostrar la imagen satelital real del lote en la vista principal, con su atribución.
- **Do** acompañar cada estado con ícono y palabra, y cada cifra con unidad y procedencia.
- **Do** usar íconos Lucide de 1,5 px solo donde ayudan a escanear (capas, actores, estados, riesgos, acciones).
- **Do** reservar el movimiento para los seis momentos autorizados y respetar movimiento reducido.
- **Do** tematizar selección, foco, caret y barras de desplazamiento con la paleta.

### Don't:
- **Don't** usar brillos, neón, glow, degradados ni glassmorphism.
- **Don't** usar celeste fuera de agua.
- **Don't** inventar imágenes de "falso color" ni capas: solo productos reales de NASA o Copernicus, con su nombre.
- **Don't** poner íconos en títulos, cifras o viñetas, ni íconos sueltos sin texto.
- **Don't** animar entradas en cada sección, contar números desde cero ni usar rebotes o elásticos.
- **Don't** usar tarjetas como estructura, porcentajes de confianza, medidores ni anillos de progreso.
- **Don't** disfrazar la interfaz de consola, radar o cabina: el mundo satelital aporta paleta, tipo y gestos, no los controles.
