# Spec Delta

## Purpose

Calcula de forma determinista el margen bruto por cultivo, campaña y escenario, el VAN en el horizonte del actor y el capital de trabajo mensual de cada rotación, usando solo parámetros económicos explícitos con fuente y fecha.

## ADDED Requirements

### Requirement: Margen bruto por cultivo y escenario
El sistema MUST calcular el margen bruto de cada cultivo de renta en un escenario como: rinde (t/ha según la clase de año de la estación del cultivo) × precio neto de retención − costos directos − costo de cosecha − comercialización − flete, todo en USD/ha y con procedencia DERIVED que lista los parámetros usados.

#### Scenario: Margen de soja de primera en año normal
- **GIVEN** parámetros de ejemplo: rinde NORMAL 3.5 t/ha, precio FOB 300 USD/t, retención 26 %, costos directos 250 USD/ha, cosecha 8 % del ingreso neto, comercialización 3 % del ingreso neto, flete 20 USD/t
- **WHEN** se calcula el margen en un escenario NORMAL
- **THEN** el ingreso neto es 777 USD/ha y el margen es 777 − 250 − 62.16 − 23.31 − 70 = 371.53 USD/ha

#### Scenario: Clase de año por estación
- **GIVEN** un escenario cuya clase de invierno es DRY y la de verano es WET
- **WHEN** se calcula el margen de trigo y de soja de segunda de la misma campaña
- **THEN** el trigo usa el rinde DRY y la soja de segunda el rinde WET

### Requirement: Cultivo de servicio como costo sin ingreso
Un cultivo de servicio MUST aportar solo costos (implantación, semilla y secado declarados en sus costos directos) y MUST NOT requerir precio, rinde ni retención.

#### Scenario: Centeno sin precio
- **GIVEN** parámetros sin precio de centeno y con costos directos de centeno
- **WHEN** se calcula el margen de una campaña con centeno y soja
- **THEN** el cálculo no falla y el margen del centeno es el negativo de sus costos directos

### Requirement: Base de precio y retención
Cada precio MUST declarar su base: FOB (la retención se descuenta) o disponible/FAS (la retención ya está incluida y MUST NOT descontarse de nuevo). La retención MUST estar en [0, 1).

#### Scenario: Precio disponible no se retiene dos veces
- **GIVEN** un precio de maíz con base disponible y retención declarada 12 %
- **WHEN** se calcula el ingreso neto
- **THEN** el ingreso neto es rinde × precio, sin descontar el 12 %, y la salida registra que la retención es informativa

### Requirement: Ajuste por estado hídrico
El cálculo MUST aceptar, por (cultivo, posición, escenario), un ajuste hídrico: `NOT_SOWN` hace que el cultivo no aporte ingresos ni costos en ese escenario, y `FORCE_DRY` hace que use el rinde de la clase DRY aunque el escenario sea de otra clase. Sin ajuste, el cálculo usa la clase del escenario. El ajuste aplicado MUST quedar registrado en la salida.

#### Scenario: Soja de segunda no sembrada
- **GIVEN** un ajuste NOT_SOWN para soja de segunda en el escenario 2008
- **WHEN** se calcula el margen de la campaña trigo + soja de segunda en 2008
- **THEN** el margen es el del trigo solo y la salida registra el ajuste para (SOY_2ND, 2008)

### Requirement: Margen por campaña y arrendamiento
El margen de una campaña MUST ser la suma de los márgenes de sus cultivos menos el arrendamiento si está presente. El arrendamiento es opcional, en USD/ha/año o en quintales de soja/ha/año convertidos con el precio neto de soja de los mismos parámetros. Si falta, MUST tomarse como ausente y la salida MUST indicar `lease_included=false`.

#### Scenario: Arrendamiento en quintales
- **GIVEN** un arrendamiento de 15 qq/ha de soja y un precio neto de soja de ejemplo de 222 USD/t
- **WHEN** se calcula el margen de la campaña
- **THEN** se restan 333 USD/ha y la procedencia del término cita el precio de soja usado

#### Scenario: Sin arrendamiento
- **WHEN** los parámetros no traen arrendamiento
- **THEN** el margen de campaña no resta nada y la salida tiene `lease_included=false`

### Requirement: Margen esperado ponderado
El margen esperado de cada posición del ciclo MUST ser la suma ponderada de sus márgenes de campaña sobre los escenarios climáticos con sus pesos. La suma MUST hacerse en orden estable de escenarios y con suma compensada.

#### Scenario: Pesos uniformes
- **GIVEN** tres escenarios con pesos 1/3 y márgenes 100, 200 y 600 USD/ha
- **WHEN** se calcula el margen esperado
- **THEN** el resultado es 300 USD/ha

### Requirement: VAN con repetición de ciclo y promedio de fases
El VAN MUST calcularse para horizonte H y tasa i como el promedio, sobre las L fases posibles de inicio del ciclo, de Σ_{t=1..H} E[Margen de la posición de ese año]/(1+i)^t, repitiendo el ciclo hasta cubrir H y truncando el último ciclo parcial. El resultado MUST ser independiente del orden en que se listan las campañas.

#### Scenario: Ciclo parcial con H=1
- **GIVEN** maíz/soja con márgenes esperados 400 (maíz) y 300 (soja) USD/ha, H=1 e i=0.1
- **WHEN** se calcula el VAN
- **THEN** el VAN es (400 + 300) / 2 / 1.1 = 318.18 USD/ha

#### Scenario: Orden de campañas irrelevante
- **WHEN** se calcula el VAN de [maíz], [soja] y de [soja], [maíz] con H=3
- **THEN** ambos VAN son idénticos

#### Scenario: Tasa cero
- **GIVEN** i=0 y H=4 con una rotación de un solo cultivo de margen esperado 250 USD/ha
- **WHEN** se calcula el VAN
- **THEN** el VAN es 1000 USD/ha

### Requirement: Márgenes por escenario disponibles para el Riesgo
La salida MUST exponer, para cada posición del ciclo y cada escenario, el margen de campaña con el escenario identificado por año, para que rotation-engine calcule el Riesgo sin recalcular la economía.

#### Scenario: Matriz completa
- **GIVEN** una rotación de 2 campañas y 30 escenarios
- **WHEN** se calcula la economía
- **THEN** la salida trae 60 márgenes identificados por (posición, año)

### Requirement: Capital de trabajo mensual
El sistema MUST calcular, para cada posición del ciclo, los egresos e ingresos esperados por mes de campaña (12 meses desde el mes de inicio supuesto) según un calendario supuesto de egresos por cultivo y un desfase de cobro, y MUST reportar el pico de necesidad acumulada (máximo de egresos acumulados menos ingresos acumulados, no negativo) en USD/ha.

#### Scenario: Pico antes de la cosecha
- **GIVEN** soja de primera con costos directos repartidos en los meses de siembra según el calendario supuesto y cobro a la cosecha más el desfase
- **WHEN** se calcula el capital de trabajo
- **THEN** el pico es igual a la suma de egresos acumulados hasta el mes previo al cobro

#### Scenario: Arrendamiento adelantado
- **GIVEN** un arrendamiento pagado en el mes 1 de campaña según el supuesto de calendario
- **WHEN** se calcula el capital de trabajo
- **THEN** el pico aumenta exactamente en el monto del arrendamiento

### Requirement: Parámetros faltantes como error tipado
Si falta un parámetro requerido para algún cultivo de la rotación (rinde de una clase, precio, retención, costos directos, cosecha, comercialización, flete o calendario de egresos), el cálculo de esa rotación MUST fallar con un error tipado que liste todos los pares (cultivo, parámetro) faltantes, sin usar valores por defecto. Un parámetro presente con valor 0 y procedencia MUST aceptarse.

#### Scenario: Falta el rinde DRY de trigo
- **GIVEN** parámetros sin rinde DRY de trigo y sin flete de maíz
- **WHEN** se calcula la economía de trigo/soja de segunda → maíz
- **THEN** el error tipado lista (WHEAT, yield_dry) y (MAIZE_EARLY, freight) en una sola falla

#### Scenario: Cero explícito
- **GIVEN** comercialización = 0 con procedencia USER_INPUT
- **WHEN** se calcula el margen
- **THEN** el cálculo usa 0 y no reporta faltante

### Requirement: Parámetros con fuente y fecha en la salida
Cada término monetario de la salida MUST conservar la procedencia y fecha de referencia de los parámetros de origen. Si los parámetros tienen fechas de referencia distintas entre sí, la salida MUST incluir una advertencia con la fecha más antigua y la más reciente.

#### Scenario: Fechas mezcladas
- **GIVEN** precio de soja con fecha 2026-11-01 y costos con fecha 2026-06-15
- **WHEN** se calcula la economía
- **THEN** la salida incluye una advertencia con ambas fechas
