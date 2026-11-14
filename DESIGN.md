---
name: Rastrojo
description: Comparador de rotaciones con datos NASA para la zona núcleo, con el lenguaje de una carta de suelos impresa.
colors:
  # Superficies (papel de carta)
  paper: "#F4EEE2"
  paper-raised: "#FBF8F1"
  paper-sunk: "#E9E0CE"
  rule: "#C9B99C"
  # Tinta
  ink: "#231A12"
  ink-soft: "#5C4C3B"
  # Marca: horizontes del suelo
  horizon-a: "#4A3423"
  rastrojo: "#B8862B"
  rastrojo-ink: "#86601A"
  # Datos NASA y agua
  agua: "#2C6A88"
  agua-wash: "#D7E4E8"
  # Estados hídricos (siempre acompañados de texto o patrón)
  state-feasible: "#3E6E33"
  state-risky: "#86601A"
  state-not-feasible: "#A23B26"
  state-unknown: "#6F665A"
  # Series de cultivos (franja de campañas)
  crop-soy: "#6E8B3D"
  crop-maize: "#D2A32C"
  crop-wheat: "#A86B2D"
  crop-vetch: "#7B5C86"
  crop-rye-oat: "#5E8C7A"
  bare-soil: "#E9E0CE"
typography:
  display:
    fontFamily: "Newsreader, 'Source Serif 4', Georgia, serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Newsreader, 'Source Serif 4', Georgia, serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.15
  title:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "'Atkinson Hyperlegible Next', 'Atkinson Hyperlegible', system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0.04em"
  figure:
    fontFamily: "'IBM Plex Mono', ui-monospace, monospace"
    fontSize: "1.125rem"
    fontWeight: 500
    lineHeight: 1.3
  place:
    fontFamily: "Newsreader, 'Source Serif 4', Georgia, serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.3
rounded:
  none: "0px"
  sm: "2px"
  md: "4px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
  xxl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.horizon-a}"
    textColor: "{colors.paper}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "12px 20px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  button-secondary:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "12px 20px"
    height: "44px"
  panel:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "24px"
  ranking-row:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    padding: "16px 24px"
    height: "72px"
  ranking-row-current:
    backgroundColor: "{colors.paper-sunk}"
    textColor: "{colors.ink}"
  badge-observed:
    backgroundColor: "{colors.agua-wash}"
    textColor: "{colors.agua}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "2px 6px"
  badge-assumption:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.rastrojo-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "2px 6px"
  input-slider:
    backgroundColor: "{colors.paper-sunk}"
    textColor: "{colors.ink}"
    height: "44px"
---

# Design System: Rastrojo

## Overview

**Creative North Star: "La carta de suelo del lote"**

Rastrojo se ve como una lámina de la carta de suelos que un agrónomo despliega sobre el capó de la camioneta: papel cálido, tinta parda, líneas finas de cartografía y una leyenda que explica cada color. La interfaz es una herramienta de trabajo (modo Operate): la navegación, los controles y las tablas son los estándar de la web, y el mundo de la carta aporta solo cuatro cosas: tipografía, paleta, densidad y un gesto propio. Nada de texturas de papel simuladas ni ornamentos de mapa antiguo.

Está diseñada primero para proyector en un aula iluminada (fondo claro, tipografía grande, contraste alto) y después se adapta al celular. La densidad es la de una lámina técnica: mucha información ordenada en una grilla firme, separada por filetes de 1 px en lugar de tarjetas. El dato manda; la marca vive en los detalles de tinta, en la leyenda y en la franja de campañas.

El gesto propio es **la franja de campañas**: cada rotación se dibuja como una franja horizontal de meses, igual que los horizontes en un corte de suelo, con los cultivos en sus colores, el suelo desnudo con rayado cartográfico y las marcas de helada y déficit hídrico encima. Cuando cambia el actor, las filas se reordenan con un movimiento corto y un indicador de cambio de posición.

**Key Characteristics:**
- Fondo papel claro, tinta parda; jamás negro puro ni blanco puro.
- Filetes de 1 px y espacio en lugar de tarjetas y sombras.
- Serif editorial para títulos y topónimos, sans hiperlegible para todo lo operativo, mono solo para cifras y unidades.
- Cada estado y cada procedencia con texto o patrón, además del color.
- Una leyenda visible siempre que haya color con significado, como en una carta impresa.

## Colors

Paleta de tierra y tinta con un solo azul, reservado para agua y datos satelitales.

### Primary
- **Horizonte A** (#4A3423): el pardo oscuro del horizonte superficial. Botón primario, barra superior, títulos de sección sobre papel. Es el color de marca.

### Secondary
- **Rastrojo** (#B8862B): el ocre del rastrojo. Solo como relleno (barras, franjas, selección, foco) y en texto grande; nunca texto chico sobre papel (contraste 2,8:1).
- **Rastrojo tinta** (#86601A): variante para texto y bordes (4,9:1 sobre papel). También es el color de estado RISKY y de los supuestos.

### Tertiary
- **Agua** (#2C6A88): todo lo que viene del satélite o habla de agua: badge OBSERVED, capa SMAP, curvas de humedad, balance hídrico. Con **Agua lavada** (#D7E4E8) como fondo de badge y de áreas de rango.

### Neutral
- **Papel** (#F4EEE2): fondo de página.
- **Papel elevado** (#FBF8F1): paneles, tabla de ranking, campos.
- **Papel hundido** (#E9E0CE): fila de la rotación actual, pista de sliders, suelo desnudo en la franja.
- **Filete** (#C9B99C): líneas divisorias de 1 px y curvas de nivel del marco del mapa. Nunca para texto.
- **Tinta** (#231A12): texto principal (14,8:1).
- **Tinta suave** (#5C4C3B): texto secundario, unidades, metadatos (7,1:1).

### Estados hídricos
- **Factible** (#3E6E33), **Riesgoso** (#86601A), **No factible** (#A23B26), **Desconocido** (#6F665A). Siempre con su palabra al lado ("Factible", "Riesgoso", "No factible", "Desconocido") y, en la franja, con patrón: liso, rayado fino, rayado cruzado, punteado.

### Series de cultivos
- Soja (#6E8B3D), maíz (#D2A32C), trigo (#A86B2D), vicia (#7B5C86), centeno y avena (#5E8C7A), suelo desnudo (#E9E0CE con rayado diagonal en Filete).

### Named Rules
**La regla de la leyenda.** Todo color con significado aparece en una leyenda visible en la misma vista. Si no hay leyenda, el color no significa nada y debe ser neutral.

**La regla del azul único.** El azul Agua se usa solo para agua y para dato satelital observado. Ningún botón, link decorativo ni acento es azul.

## Typography

**Display Font:** Newsreader (con Source Serif 4, Georgia)
**Body Font:** Atkinson Hyperlegible Next (con Atkinson Hyperlegible, system-ui)
**Label/Mono Font:** IBM Plex Mono, solo para cifras con unidad, años y coordenadas

**Character:** la serif da la voz de la carta impresa y de los topónimos; la Atkinson, diseñada para máxima legibilidad, carga todo lo que se lee rápido desde el fondo del aula. Las tres son OFL y se autoalojan.

### Hierarchy
- **Display** (600, 3rem, 1,05): nombre del lote en la cabecera del mapa. Una vez por pantalla.
- **Headline** (600, 1,75rem, 1,15): títulos de panel ("Rotaciones comparadas", "Evidencia").
- **Title** (700, 1,25rem, 1,25): nombre de cada rotación en el ranking.
- **Body** (400, 1,125rem, 1,5): explicaciones; medida máxima 68ch.
- **Label** (700, 0,875rem, tracking 0,04em, versalitas solo en leyendas de mapa): ejes, encabezados de tabla, badges.
- **Figure** (Plex Mono 500, 1,125rem, cifras tabulares): USD/ha, mm, °C, años. La unidad va en Tinta suave y un punto más chica.
- **Place** (Newsreader itálica 400, 1rem): topónimos y etiquetas sobre el mapa, como en la cartografía impresa.

### Named Rules
**La regla de la cifra con unidad.** Ninguna cifra aparece sin unidad ni sin su badge de procedencia a mano. Formato argentino: coma decimal, punto de miles.

**La regla de la mono justificada.** La mono se usa solo para medidas, años y coordenadas. Nunca para títulos ni para "dar aire técnico".

## Layout

Grilla de 12 columnas con márgenes de 40 px en 1920 y 24 px en 1280. Pantalla principal en proyector: mapa del lote a la izquierda (5 columnas, alto completo), ranking de rotaciones con sus franjas de campañas a la derecha (7 columnas), y debajo del ranking el panel de evidencia y procedencia de la rotación seleccionada. El selector de actor y los sliders H, α y λ viven en una barra fija sobre el ranking, porque son el control que se usa en vivo durante el pitch. El simulador de WhatsApp se abre como panel lateral derecho que empuja el contenido, no como modal.

En celular (390 px) el orden es: actor, ranking con franjas compactas, mapa colapsable, evidencia. Ritmo vertical en múltiplos de 8 px; más espacio sobre un título que debajo. Separación entre zonas con filetes de 1 px en Filete y 40 px de aire, no con tarjetas.

## Elevation & Depth

Plano por defecto, como el papel. La profundidad se marca con tono (papel, papel elevado, papel hundido) y con filetes. La única sombra es para elementos que flotan sobre el mapa o la página (tooltips de procedencia, panel de chat): `box-shadow: 0 2px 8px rgba(35, 26, 18, 0.12), 0 1px 2px rgba(35, 26, 18, 0.08)`.

### Named Rules
**La regla del papel plano.** Nada en reposo tiene sombra. La sombra aparece solo en lo que flota temporalmente.

## Shapes

Esquinas casi rectas, como una lámina recortada: 0 px en paneles y tablas, 2 px en botones, badges y campos, 4 px como máximo. Bordes de 1 px en Filete. El marco del mapa lleva un doble filete fino (1 px Tinta y 1 px Filete con 3 px de separación), igual que el marco de una carta impresa, con la escala gráfica y el norte en la esquina inferior. Ese marco es el único guiño cartográfico explícito.

## Components

### Buttons
- **Shape:** casi rectos (2 px), alto mínimo 44 px.
- **Primary:** Horizonte A con texto Papel, Label 700.
- **Hover / Focus:** hover a Tinta; foco con anillo de 2 px en Rastrojo y 2 px de separación. Transición de 120 ms ease-out.
- **Secondary:** Papel elevado con borde de 1 px en Tinta suave.

### Selector de actor
- Control segmentado estándar con cuatro opciones (Propietario, Arrendatario, Cooperativa, Banco). Seleccionado: fondo Horizonte A, texto Papel. Debajo, los sliders H (años), α (peso del suelo) y λ (aversión al riesgo) con su valor en Figure y una línea de ayuda en lenguaje simple.

### Ranking de rotaciones (componente firma)
- Tabla, no tarjetas. Cada fila: posición, nombre de la rotación (Title), puntaje en USD/ha (Figure), desglose en barra apilada fina (margen, suelo, riesgo), estado hídrico con palabra, ΔSuelo, años con pérdida "x de N", y debajo **la franja de campañas**.
- La rotación actual lleva el rótulo "Actual" en texto y fondo Papel hundido.
- Al cambiar actor o slider, las filas se reordenan con una animación FLIP de 280 ms (ease-out exponencial) y un indicador "+1" o "−2" en Rastrojo tinta durante 2 s. Con movimiento reducido: sin desplazamiento, solo el indicador.

### Franja de campañas
- Una fila de 12 o 24 celdas (meses del ciclo) con los cultivos en sus colores; el suelo desnudo con rayado diagonal; marcas de helada y déficit hídrico como íconos SVG de trazo de 1,5 px en No factible y Agua; el rango histórico (años secos a húmedos) como banda Agua lavada. Leyenda siempre visible en la cabecera del ranking.

### Badges de procedencia
- OBSERVED: Agua sobre Agua lavada. DERIVED: Horizonte A sobre Papel hundido. ASSUMPTION: Rastrojo tinta con borde punteado de 1 px y el id (A-WAT-01). USER_INPUT: Tinta con borde liso. Siempre con la palabra abreviada (OBS, DER, SUP, USU) además del color. Tooltip accesible por teclado con dataset, variable, período y resolución.

### Mapa
- Leaflet con capas GIBS. Leyenda de cada capa con unidad, resolución y limitación ("SMAP L4 · ~9 km · modelo asimilado, no mide el lote"). Topónimos en Place. Selector de fecha estándar.

### Panel de evidencia
- Lista con filetes, no tarjetas: cada evidencia con dataset, variable, período, valor con unidad e interpretación en una frase. Faltantes con el estado "Desconocido" y qué haría falta para conseguir el dato.

### Leyendas fijas
- "Apoya, no reemplaza al agrónomo" y "Escenarios históricos, no predicción" en el pie de la vista principal, en Body y Tinta suave, siempre visibles.

## Do's and Don'ts

### Do:
- **Do** usar Papel (#F4EEE2) como fondo y Tinta (#231A12) como texto; verificar 4,5:1 en todo texto chico.
- **Do** acompañar cada color de estado con su palabra y, en la franja, con su patrón.
- **Do** mostrar la unidad y el badge de procedencia junto a cada cifra.
- **Do** separar zonas con filetes de 1 px y espacio.
- **Do** tematizar la selección de texto (Rastrojo al 30 %), el caret, el foco y las barras de desplazamiento con la paleta.

### Don't:
- **Don't** usar tarjetas iguales de ícono, título y texto como estructura, ni tarjetas anidadas.
- **Don't** poner etiquetas pequeñas (kickers) sobre los títulos.
- **Don't** usar texturas de papel, manchas, mapas antiguos ni tipografías "western" o de mapa del tesoro: el mundo es la carta técnica, no la nostalgia.
- **Don't** usar azul fuera de agua y dato satelital.
- **Don't** mostrar porcentajes de confianza, gauges ni anillos de progreso.
- **Don't** usar emoji como íconos; un único set SVG de trazo constante.
- **Don't** usar degradados en texto ni brillos.
